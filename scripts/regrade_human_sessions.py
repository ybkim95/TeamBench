"""Re-grade human-eval Solo/Hybrid/Team sessions against the deterministic grader.

Pulls each session's `sharedArtifacts.finalWorkspace.files` from Firebase,
materializes the workspace into a temp dir using the canonical task layout
(by inverting the Firebase key encoding `path.replace(/[.\/\[\]#$]/g, '_')`
against the task's known initialWorkspace keys), then runs the task's
grade.sh and records pass/partial.

Output: shared/paper/human_eval_regrade.json with per-session results.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from collections import defaultdict
from pathlib import Path

REPO = Path("/u/ybkim95/TeamBench")
TASKS_DIR = REPO / "tasks"
DB = "https://ivory-plane-406700-default-rtdb.firebaseio.com"

INVALID = [re.compile(p, re.IGNORECASE) for p in [
    r"^test\d*$", r"^admin\d*$", r"^team[_\-]?test[_\-]?\d*$",
    r"^probe.*$", r"^[a-z]$",
    r"^test\d+@google\.com$", r"^admin\d+@google\.com$",
    r"^test\d+@admin\d+\.edu$", r"^admin\d+@admin\d+\.edu$",
    r"^team[_\-]?test[_\-]?\d+@google\.com$", r"^probe\d*@.*$",
]] + [re.compile(r"^[a-z]{1,3}$")]
EMAIL_SHAPE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def valid(name, email):
    n = (name or "").strip().lower()
    e = (email or "").strip().lower()
    if not e or not EMAIL_SHAPE.match(e) or len(n) < 2 or n == e:
        return False
    for p in INVALID:
        if p.match(n) or p.match(e):
            return False
    return True


def fb_key(path: str) -> str:
    """Match the JS encoding: replace [./\\[\\]#$] with _."""
    return re.sub(r"[./\[\]#$]", "_", path)


_GEN_CACHE: dict = {}


def get_generated(task_id: str):
    if task_id in _GEN_CACHE:
        return _GEN_CACHE[task_id]
    sys.path.insert(0, str(REPO))
    try:
        from generators.registry import get_generator
        g = get_generator(task_id)
        res = g.generate(0)
    except Exception as e:
        res = None
    _GEN_CACHE[task_id] = res
    return res


def list_workspace_paths(task_id: str) -> list[str]:
    """Canonical workspace file paths for a task (from generator at seed 0)."""
    res = get_generated(task_id)
    if res is None:
        return []
    return list((res.workspace_files or {}).keys())


def materialize_session(task_id: str, files_obj: dict, dest: Path) -> dict:
    """Write the human's final workspace into dest using canonical paths.

    Returns {n_matched, n_unmatched, unmatched_keys}.
    """
    canonical = list_workspace_paths(task_id)
    key_to_path = {fb_key(p): p for p in canonical}
    n_matched = 0
    unmatched = []
    for fb_k, entry in files_obj.items():
        content = entry.get("content", "") if isinstance(entry, dict) else ""
        if content is None:
            content = ""
        path = key_to_path.get(fb_k)
        if path is None:
            path = guess_path(fb_k)
            unmatched.append(fb_k)
        # Clamp to workspace: strip leading slash and any ".." segments.
        path = path.lstrip("/")
        path = path.replace("..", "_")
        target = dest / path
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        except (PermissionError, OSError):
            continue
        n_matched += 1 if path in canonical else 0
    return {"n_files": len(files_obj), "n_matched": n_matched,
            "n_unmatched": len(unmatched), "unmatched_keys": unmatched[:8]}


_EXT_RE = re.compile(r"_(py|md|json|yaml|yml|toml|txt|sh|cfg|ini|go|js|ts|tsx|html|css|sql)$")


def guess_path(key: str) -> str:
    """Best-effort fallback path reconstruction from a Firebase key."""
    p = key
    m = _EXT_RE.search(p)
    if m:
        ext = m.group(1)
        p = p[: m.start()] + "." + ext
    # Heuristic: dunder collapsed to /__
    p = p.replace("___", "/__")
    p = p.replace("_", "/", 1) if "/" not in p and p.count("_") > 0 else p
    return p


def run_grader(task_id: str, workspace: Path) -> dict:
    """Run the task's grade.sh against the materialized workspace.

    Mirrors how the human-eval backend's /grade endpoint invokes graders:
    grade.sh /workspace /reports /submission /task
    """
    task_dir = TASKS_DIR / task_id
    grade_sh = task_dir / "grade.sh"
    if not grade_sh.is_file():
        return {"status": "no_grader"}

    with tempfile.TemporaryDirectory() as td_str:
        td = Path(td_str)
        reports = td / "reports"
        submission = td / "submission"
        reports.mkdir()
        submission.mkdir()

        # Write reports/expected.json from the generator output (this is
        # what grade.sh consults for the answer key).
        gen = get_generated(task_id)
        if gen is not None and getattr(gen, "expected", None):
            (reports / "expected.json").write_text(
                json.dumps(gen.expected))

        # Some tasks have a setup.sh that prepares additional files.
        setup_sh = task_dir / "setup.sh"
        if setup_sh.is_file():
            try:
                subprocess.run(
                    ["bash", str(setup_sh), str(workspace), str(reports),
                     str(submission), str(task_dir)],
                    check=False, capture_output=True, timeout=60)
            except subprocess.TimeoutExpired:
                pass

        # Pre-seed attestation (matches backend default).
        att = submission / "attestation.json"
        if not att.exists():
            att.write_text(json.dumps(
                {"verdict": "pass", "source": "human_eval_default"}))

        # The graders invoke `python3 -m pytest`. The user's site-packages
        # at ~/.local/lib/python3.10/site-packages/_pytest contains a broken
        # install (NameError on built-in exceptions), so without disabling
        # user site we get false `tests_failing` everywhere. We pin python3
        # to the project venv binary and disable user-site to match the
        # human-eval Docker container's fresh-env semantics.
        venv_bin = "/u/ybkim95/TeamBench/.venv/bin"
        env = os.environ.copy()
        env["PYTHONNOUSERSITE"] = "1"
        env["PATH"] = f"{venv_bin}:{env.get('PATH','')}"
        env["PYTHONPATH"] = ""
        try:
            r = subprocess.run(
                ["bash", str(grade_sh), str(workspace), str(reports),
                 str(submission), str(task_dir)],
                capture_output=True, timeout=180, text=True, env=env)
        except subprocess.TimeoutExpired:
            return {"status": "timeout"}

        score_path = reports / "score.json"
        score = None
        if score_path.is_file():
            try:
                score = json.loads(score_path.read_text())
            except Exception:
                score = None
        return {
            "status": "graded",
            "exit_code": r.returncode,
            "score": score,
            "stderr_tail": r.stderr[-400:] if r.stderr else "",
        }


def main():
    print("Pulling Firebase ...", file=sys.stderr)
    root = json.load(urllib.request.urlopen(
        f"{DB}/teambench_new.json", timeout=60))
    tasks = root.get("tasks", {})
    print(f"  {len(tasks)} tasks", file=sys.stderr)

    results = []
    for tid, by_mode in tasks.items():
        for mode, blob in (by_mode or {}).items():
            if mode not in ("oracle", "hybrid", "team"):
                continue
            for sid, sess in (blob or {}).get("sessions", {}).items():
                meta = sess.get("meta", {})
                if not (meta.get("phase") == "completed"
                        or meta.get("status") == "completed"):
                    continue
                # Validity gate
                parts = sess.get("participants", {}) or {}
                kept = False
                for pid, p in parts.items():
                    prof = p.get("profile", {})
                    if not valid(prof.get("name", ""), prof.get("email", "")):
                        continue
                    role = prof.get("role", "")
                    surv = p.get("survey", {}) or {}
                    if role and role in surv:
                        kept = True
                        break
                if not kept:
                    continue
                sa = sess.get("sharedArtifacts", {}) or {}
                fw = sa.get("finalWorkspace", {}) or {}
                files = fw.get("files", {}) or {}
                if not files:
                    results.append({
                        "task_id": tid, "session_id": sid, "mode": mode,
                        "human_verdict": meta.get("verdict"),
                        "regrade_status": "no_workspace_snapshot",
                    })
                    continue
                with tempfile.TemporaryDirectory() as td:
                    ws = Path(td) / "workspace"
                    ws.mkdir()
                    # Lay down the canonical workspace baseline first; then
                    # overlay the human's edited files. This is what the
                    # backend does at session start, so files the human did
                    # not edit are still present for the grader.
                    gen = get_generated(tid)
                    if gen is not None:
                        for path, content in (gen.workspace_files or {}).items():
                            p = ws / path
                            p.parent.mkdir(parents=True, exist_ok=True)
                            try:
                                p.write_text(content)
                            except (PermissionError, OSError):
                                pass
                    mat = materialize_session(tid, files, ws)
                    g = run_grader(tid, ws)
                    binary_pass = None
                    partial = None
                    if g.get("score"):
                        s = g["score"]
                        binary_pass = bool(s.get("pass"))
                        # Real partial score lives in s["secondary"]["partial_score"]
                        # for the canonical grader format.
                        sec = s.get("secondary") or {}
                        partial = (sec.get("partial_score")
                                   or s.get("partial")
                                   or s.get("score"))
                    results.append({
                        "task_id": tid, "session_id": sid, "mode": mode,
                        "human_verdict": meta.get("verdict"),
                        "regrade_status": g.get("status"),
                        "regrade_pass": binary_pass,
                        "regrade_partial": partial,
                        "exit_code": g.get("exit_code"),
                        "n_files": mat["n_files"],
                        "n_matched": mat["n_matched"],
                        "n_unmatched": mat["n_unmatched"],
                        "unmatched_keys": mat["unmatched_keys"],
                        "stderr_tail": g.get("stderr_tail", ""),
                    })
                print(f"  {mode} {tid} {sid[:18]} -> {results[-1].get('regrade_pass')} ({results[-1].get('regrade_status')})",
                      file=sys.stderr, flush=True)

    out_path = REPO / "shared/paper/human_eval_regrade.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2))
    print(f"Wrote {out_path}", file=sys.stderr)

    # Summary
    by_mode_total = defaultdict(int)
    by_mode_pass = defaultdict(int)
    by_mode_failed_grader = defaultdict(int)
    by_mode_no_grader = defaultdict(int)
    human_verdict_pass = defaultdict(int)
    for r in results:
        m = r["mode"]
        by_mode_total[m] += 1
        if r.get("human_verdict") == "pass":
            human_verdict_pass[m] += 1
        if r.get("regrade_status") == "graded":
            if r.get("regrade_pass"):
                by_mode_pass[m] += 1
        elif r.get("regrade_status") == "no_grader":
            by_mode_no_grader[m] += 1
        else:
            by_mode_failed_grader[m] += 1

    print("\n=== Re-grade summary ===", file=sys.stderr)
    for m in ("oracle", "hybrid", "team"):
        n = by_mode_total[m]
        p = by_mode_pass[m]
        ng = by_mode_no_grader[m]
        fail = by_mode_failed_grader[m]
        hv = human_verdict_pass[m]
        rate = (100 * p / n) if n else 0
        print(f"  {m:7s}: human_verdict_pass={hv}/{n} | regrade_pass={p}/{n} ({rate:.1f}%) | no_grader={ng} | grader_error={fail}",
              file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
