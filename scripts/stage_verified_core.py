#!/usr/bin/env python3
"""Stage a verified-core task from upstream instead of from a vendored copy.

Why staging changes
-------------------
The task scraper copied only the files a pull request touched. That is the single
root cause behind every corpus-level symptom measured earlier: the package is in
pieces, conftest.py is absent, and the grader's test target cannot be collected,
so no GH task passed under any model and the maintainers' own merged fix was
worth +2.0 pp. Restoring individual missing files chases the symptom; the fix is
to stop copying and start checking out.

Checking out also removes a licensing problem that copying created. 645 vendored
workspaces ship zero upstream LICENSE files, and the upstreams include AGPL-3.0,
GPL-3.0 and LGPL-3.0 projects, all currently under the repository's blanket MIT.
Nothing copyleft is in the published subset today, but the full corpus release the
paper promises would expose 21 such tasks. A task that names `repo` and `base_sha`
and fetches at run time distributes no upstream code at all.

What a staged task looks like
-----------------------------
    <dest>/workspace          the repo at base_sha, unmodified
    <cache>/deps/<repo>@<sha> third-party dependencies, shared across instances

The dependency set is pinned, not re-resolved: it comes from the freeze recorded
by build_verified_core.py at the moment the task was proved to discriminate. It
is installed with `pip install --target`, which is relocatable, so the same
directory can be mounted read-only into a network-isolated container. The package
under test is NOT installed; `python -m pytest` run from the workspace root puts
the source tree first on sys.path, which is the copy the agent edits and the
grader must measure.

Usage:
  python scripts/stage_verified_core.py --task GH140_marshmallow_2874 --dest /tmp/t
  python scripts/stage_verified_core.py --task ... --dest /tmp/t --check
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS = os.path.join(REPO, "tasks")
Q = os.path.join(REPO, "shared", "paper", "quality")
CACHE = os.path.join(REPO, ".cache", "core")


def sh(cmd, cwd=None, timeout=1800, env=None):
    return subprocess.run(cmd, shell=isinstance(cmd, str), cwd=cwd,
                          capture_output=True, text=True, timeout=timeout,
                          env={**os.environ, **(env or {})})


def load_core() -> dict:
    """Every verified task from every shard of the build, newest wins."""
    import glob as _glob
    out = {}
    # Oldest shard first so a later, better-instrumented run wins: the earliest
    # shards predate the environment freeze and the shadowing guard, and staging
    # a task from a row with no freeze installs almost no dependencies.
    shards = sorted(_glob.glob(os.path.join(Q, "verified_core*.json")),
                    key=os.path.getmtime)
    for p in shards:
        try:
            rows = json.load(open(p))
        except Exception:
            continue
        for r in rows:
            if not r.get("verified"):
                continue
            prev = out.get(r["task"])
            # never replace a row that has a freeze with one that does not
            if prev and prev.get("env_freeze") and not r.get("env_freeze"):
                continue
            out[r["task"]] = r
    return out


def source_roots(ws: str) -> list:
    """Directories that must be on sys.path for the checkout to be importable.

    Deliberately not `pip install -e .`: an editable install is not relocatable,
    and the point of staging is a dependency directory that can be mounted
    read-only into a container at a fixed path. Putting the source on the path
    instead keeps the package under test as the working tree the agent edits.

    `src/` matters. marshmallow, attrs, urllib3 and others use a src layout, so
    `import marshmallow` from the workspace root fails and the grader's C5
    ("source modules import without error") goes red for a reason that has
    nothing to do with the submission.
    """
    roots = [ws]
    src = os.path.join(ws, "src")
    if os.path.isdir(src) and any(
            os.path.isfile(os.path.join(src, d, "__init__.py"))
            for d in os.listdir(src) if os.path.isdir(os.path.join(src, d))):
        roots.insert(0, src)
    return roots


def deps_dir(repo: str, sha: str) -> str:
    return os.path.join(CACHE, "deps", repo.replace("/", "_") + "@" + sha[:12])


def ensure_deps(row: dict, timeout: int) -> str:
    """Build the dependency environment once per (repo, base_sha).

    A venv rather than `pip install --target`. The graders call the bare `pytest`
    console script, which a --target install does not create, so the run would
    silently fall through to whatever pytest happened to be on PATH and measure
    the wrong environment.

    Relocation is a non-issue because the cache is bind-mounted into the sandbox
    at the SAME absolute path it has on the host, so the interpreter paths baked
    into pyvenv.cfg and the console-script shebangs stay correct.
    """
    d = deps_dir(row["repo"], row["sha"])
    stamp = os.path.join(d, ".complete")
    if os.path.isfile(stamp):
        return d
    os.makedirs(os.path.dirname(d), exist_ok=True)
    sh([sys.executable, "-m", "venv", d], timeout=timeout)
    pip = os.path.join(d, "bin", "pip")
    sh([pip, "install", "-q", "-U", "pip", "setuptools", "wheel"], timeout=timeout)
    frozen = row.get("env_freeze") or []
    if not frozen:
        # Older shards of the build predate the freeze. Fall back to the minimum
        # that lets a suite run; re-running that task through
        # build_verified_core.py records the real set.
        frozen = ["pytest", "pytest-mock", "pytest-asyncio"]
    if sh([pip, "install", "-q", *frozen], timeout=timeout).returncode:
        # One at a time, so a single unsatisfiable pin does not lose the rest.
        for pkg in frozen:
            sh([pip, "install", "-q", pkg], timeout=timeout)
    open(stamp, "w").write("\n".join(frozen))
    return d


def stage(task: str, dest: str, timeout: int = 1800) -> dict:
    core = load_core()
    row = core.get(task)
    if not row:
        return {"task": task, "status": "not_in_verified_core"}
    ws = os.path.join(dest, "workspace")
    if os.path.isdir(ws):
        shutil.rmtree(ws)
    os.makedirs(dest, exist_ok=True)
    r = sh(["git", "clone", "--quiet", "--filter=blob:none", "--no-checkout",
            f"https://github.com/{row['repo']}.git", ws], timeout=timeout)
    if r.returncode:
        return {"task": task, "status": "clone_failed", "err": r.stderr[-200:]}
    r = sh(["git", "checkout", "--quiet", row["sha"]], cwd=ws, timeout=timeout)
    if r.returncode:
        return {"task": task, "status": "checkout_failed", "err": r.stderr[-200:]}
    # The clone's own history is not part of the task and would let an agent read
    # the fix straight out of a later commit.
    shutil.rmtree(os.path.join(ws, ".git"), ignore_errors=True)
    d = ensure_deps(row, timeout)
    meta = {"task": task, "repo": row["repo"], "base_sha": row["sha"],
            "target": row["target"], "deps_dir": d,
            "source_roots": [os.path.relpath(r, dest) for r in source_roots(ws)],
            "status": "ok"}
    json.dump(meta, open(os.path.join(dest, "task_env.json"), "w"), indent=1)
    return meta


def grade(task: str, dest: str, deps: str, timeout: int = 900) -> dict:
    """Run the task's existing grader against the staged workspace."""
    ws = os.path.join(dest, "workspace")
    reports = os.path.join(dest, "reports")
    sub = os.path.join(dest, "submission")
    for p in (reports, sub):
        os.makedirs(p, exist_ok=True)
    json.dump({"task_id": task, "verdict": "pass", "checklist": []},
              open(os.path.join(sub, "attestation.json"), "w"))
    task_dir = os.path.join(TASKS, task)
    env = {"PYTHONPATH": os.pathsep.join(source_roots(ws)),
           "PATH": os.path.join(deps, "bin") + os.pathsep + os.environ.get("PATH", "")}
    try:
        sh(["bash", os.path.join(task_dir, "grade.sh"), ws, reports, sub, task_dir],
           timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    p = os.path.join(reports, "score.json")
    if not os.path.isfile(p):
        return {"status": "no_score_json"}
    sc = json.load(open(p))
    sec = sc.get("secondary") or {}
    checks = sec.get("checks") or sc.get("checklist") or []
    return {"status": "ok", "pass": bool(sc.get("pass")),
            "partial": sec.get("partial_score"),
            "n_checks": len(checks),
            "failed": [c.get("id") or c.get("note", "")[:40]
                       for c in checks if isinstance(c, dict) and not c.get("ok")]}


def three_arms(task: str, dest: str, timeout: int) -> dict:
    """Grade the staged task pristine, with tests injected, and fully fixed.

    A  pristine, grader as it stands.        Should FAIL. If it passes, the
                                             grader cannot see the bug, because
                                             the test that defines the bug is the
                                             one the PR adds and base_sha does
                                             not have it.
    B  pristine + the PR's test hunks.       Should FAIL. This is the signal.
    C  the maintainers' full fix.            Should PASS, or the task is
                                             unsolvable even by its own author.

    A task is usable iff B fails and C passes. A is reported to show how much of
    the corpus was silently unmeasurable before injection.
    """
    meta = stage(task, dest, timeout)
    if meta.get("status") != "ok":
        return {"task": task, **meta}
    ws = os.path.join(dest, "workspace")
    patch = os.path.join(TASKS, task, "reference", "patch.diff")
    sh(["git", "init", "-q"], cwd=ws)
    sh(["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"], cwd=ws)
    sh(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base"],
       cwd=ws)

    def reset():
        sh(["git", "checkout", "-q", "--", "."], cwd=ws)
        sh(["git", "clean", "-fdq"], cwd=ws)

    out = {"task": task, "repo": meta["repo"], "status": "ok"}
    out["A"] = grade(task, dest, meta["deps_dir"], timeout)
    reset()
    inj = sh(f"git apply --include='*test*' {patch!r}", cwd=ws)
    out["inject_rc"] = inj.returncode
    out["B"] = grade(task, dest, meta["deps_dir"], timeout)
    reset()
    sh(["git", "apply", patch], cwd=ws)
    out["C"] = grade(task, dest, meta["deps_dir"], timeout)
    reset()
    out["usable"] = bool(out["B"].get("pass") is False and out["C"].get("pass"))
    out["grader_blind_without_injection"] = bool(out["A"].get("pass"))
    return out


def batch(tasks: list, root: str, workers: int, timeout: int, out_path: str) -> int:
    import concurrent.futures as cf
    done = []
    if os.path.isfile(out_path):
        done = json.load(open(out_path))
        seen = {d["task"] for d in done}
        tasks = [t for t in tasks if t not in seen]
        print(f"  resuming, {len(seen)} already staged, {len(tasks)} to go", flush=True)
    print(f"tasks to stage: {len(tasks)}  (workers={workers})", flush=True)

    def one(t):
        d = os.path.join(root, t)
        try:
            return three_arms(t, d, timeout)
        except Exception as e:
            return {"task": t, "status": "error", "err": str(e)[:200]}
        finally:
            shutil.rmtree(d, ignore_errors=True)

    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(one, t): t for t in tasks}
        for i, f in enumerate(cf.as_completed(futs), 1):
            done.append(f.result())
            if i % 5 == 0 or i == len(tasks):
                json.dump(done, open(out_path, "w"), indent=1)
                u = sum(1 for d in done if d.get("usable"))
                print(f"  [{i}/{len(tasks)}] usable so far: {u}", flush=True)
    json.dump(done, open(out_path, "w"), indent=1)
    ok = [d for d in done if d.get("status") == "ok"]
    print(f"\nstaged {len(done)}   graded {len(ok)}")
    print(f"  USABLE (B fails, C passes)          : {sum(1 for d in ok if d.get('usable'))}")
    print(f"  grader blind without test injection : "
          f"{sum(1 for d in ok if d.get('grader_blind_without_injection'))} of {len(ok)}")
    print(f"\nwrote {out_path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task")
    ap.add_argument("--all", action="store_true",
                    help="stage and validate the whole verified core")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default=os.path.join(Q, "core_staged.json"))
    ap.add_argument("--dest", required=True)
    ap.add_argument("--check", action="store_true",
                    help="grade pristine, then with the reference patch applied")
    ap.add_argument("--timeout", type=int, default=1800)
    a = ap.parse_args()

    if a.all:
        tasks = sorted(load_core())
        if a.limit:
            tasks = tasks[: a.limit]
        return batch(tasks, a.dest, a.workers, a.timeout, a.out)
    if not a.task:
        ap.error("give --task or --all")

    meta = stage(a.task, a.dest, a.timeout)
    print(json.dumps(meta, indent=1))
    if meta.get("status") != "ok" or not a.check:
        return 0 if meta.get("status") == "ok" else 1

    ws = os.path.join(a.dest, "workspace")
    patch = os.path.join(TASKS, a.task, "reference", "patch.diff")
    # A commit to reset to between arms. The staged tree has no history, which
    # is deliberate: leaving .git in place would let an agent read the fix out of
    # a later commit.
    sh(["git", "init", "-q"], cwd=ws)
    sh(["git", "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"], cwd=ws)
    sh(["git", "-c", "user.email=t@t", "-c", "user.name=t",
        "commit", "-qm", "base"], cwd=ws)

    def reset():
        sh(["git", "checkout", "-q", "--", "."], cwd=ws)
        sh(["git", "clean", "-fdq"], cwd=ws)

    arms = {}
    print("\nA  pristine checkout, grader as it stands", flush=True)
    arms["A"] = grade(a.task, a.dest, meta["deps_dir"])
    print(json.dumps(arms["A"], indent=1))

    reset()
    sh(f"git apply --include='*test*' {patch!r}", cwd=ws)
    print("\nB  pristine + the PR's test hunks injected at grade time", flush=True)
    arms["B"] = grade(a.task, a.dest, meta["deps_dir"])
    print(json.dumps(arms["B"], indent=1))

    reset()
    sh(["git", "apply", patch], cwd=ws)
    print("\nC  the maintainers' full fix, tests included", flush=True)
    arms["C"] = grade(a.task, a.dest, meta["deps_dir"])
    print(json.dumps(arms["C"], indent=1))
    reset()

    print("\n  arm                                        pass   partial")
    for k, lab in (("A", "pristine, grader as it stands"),
                   ("B", "pristine + injected tests"),
                   ("C", "full reference fix")):
        print("  %s  %-38s %-6s %s" % (k, lab, arms[k].get("pass"), arms[k].get("partial")))
    works = (not arms["B"].get("pass")) and arms["C"].get("pass")
    print("\n  test injection %s" % (
        "MAKES THE TASK DISCRIMINATE" if works else "does not yet make it discriminate"))
    if arms["A"].get("pass"):
        print("  note: arm A passes, so without injection the grader cannot see the bug")
    return 0
if __name__ == "__main__":
    sys.exit(main())
