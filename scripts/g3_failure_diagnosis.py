#!/usr/bin/env python3
"""
Why does the grader reject a correct upstream fix?

For each task named, this stages the pristine workspace, turns it into the
upstream reference solution with harness/reference_apply.py, and then re-runs
the grader's own C1 (pytest) and C5 (import the source module) commands
directly, capturing their stderr.  Each failure is then classified by cause:

  missing_dependency      ModuleNotFoundError/ImportError for a package that is
                          not installed. The grader depends on an unpinned,
                          unavailable dependency; no edit to the workspace can
                          fix it.
  parameterisation_break  ImportError/NameError for a name the task generator
                          itself invented, e.g. `contextmanager_ext` or
                          `set_base`. generators/gh_deep_param.py renames Python
                          builtins and stdlib import targets, so the staged
                          workspace does not import. Also unfixable by any edit,
                          and it is self-inflicted.
  relative_import         "attempted relative import with no known parent
                          package": C5 loads a package module as a lone file.
  missing_target          the grader's pytest target does not exist.
  assertion               a real test assertion failed with the upstream fix
                          applied: the only class where the grader and the
                          upstream maintainers genuinely disagree about the code.
  other                   anything else, with the raw tail kept.

Usage:
    python3 scripts/g3_failure_diagnosis.py TASK [TASK ...] [--out FILE]
    python3 scripts/g3_failure_diagnosis.py --from-ledger 12
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
QUALITY = os.path.join(REPO_ROOT, "shared", "paper", "quality")

# Two shapes occur in this corpus:
#   pytest_out=$(pytest <targets> -x -q --tb=short 2>&1)
#   pytest_out=$(python -m pytest -x -q --tb=short 2>&1)     <- no target at all,
#       which collects the WHOLE workspace, i.e. whatever subset of the upstream
#       repo the task happens to ship.
_PYTEST_RE = re.compile(
    r"pytest_out=\$\((?:python3?\s+-m\s+)?pytest\s*(.*?)\s*-x\s+-q", re.S)
_C5_RE = re.compile(r"# .. C5:.*?for src in (.+?); do", re.S)

_SUFFIXES = ("_v2", "_impl", "_new", "_base", "_core", "_alt", "_ext", "_mod")


def grader_targets(task_dir: str) -> tuple[list[str], list[str]]:
    try:
        text = open(os.path.join(task_dir, "grade.sh"), encoding="utf-8",
                    errors="replace").read()
    except OSError:
        return [], []
    m = _PYTEST_RE.search(text)
    tests = m.group(1).split() if m else None       # None = no pytest block found
    if tests is None:
        tests = []
    elif not tests:
        tests = ["<whole workspace: grader passes no target>"]
    m2 = _C5_RE.search(text)
    srcs = m2.group(1).split() if m2 else []
    return tests, srcs


def classify(out: str) -> tuple[str, str]:
    """Return (cause, evidence line)."""
    lines = [l for l in out.splitlines() if l.strip()]
    # A SyntaxError in a workspace file is the parameteriser having rewritten a
    # Python KEYWORD: the symbol pool is collected across every language in the
    # workspace, so a Rust or TypeScript file contributes `from` or `class`, and
    # the Python renamer then emits `from_v2 decimal import ...` or
    # `class_new MyModel(...)`. Check this before the generic assertion rule,
    # which would otherwise catch the `E   SyntaxError:` line.
    for l in lines:
        if "SyntaxError" in l:
            return "syntax_error_from_parameterisation", l.strip()[:300]
    for l in reversed(lines):
        m = re.search(r"(?:ModuleNotFoundError|ImportError): (.*)", l)
        if m:
            detail = m.group(1)
            nm = re.search(r"cannot import name '([^']+)'", detail)
            if nm and any(nm.group(1).endswith(s) for s in _SUFFIXES):
                return "parameterisation_break", l.strip()[:300]
            if "attempted relative import" in detail:
                return "relative_import", l.strip()[:300]
            mod = re.search(r"No module named '([^']+)'", detail)
            if mod and any(mod.group(1).endswith(s) for s in _SUFFIXES):
                return "parameterisation_break", l.strip()[:300]
            return "missing_dependency", l.strip()[:300]
        if "attempted relative import with no known parent package" in l:
            return "relative_import", l.strip()[:300]
        m = re.search(r"NameError: name '([^']+)' is not defined", l)
        if m and any(m.group(1).endswith(s) for s in _SUFFIXES):
            return "parameterisation_break", l.strip()[:300]
        if l.startswith("E   ") and ("assert" in l or "Error" in l):
            return "assertion", l.strip()[:300]
    if re.search(r"^no tests ran", out, re.M) or "no tests ran in" in out:
        return "no_tests_collected", "no tests ran"
    if "No files were found in testpaths" in out:
        return "no_tests_collected", "No files were found in testpaths"
    if "file or directory not found" in out or "ERROR: not found" in out:
        return "missing_target", out.strip().splitlines()[-1][:300] if out.strip() else ""
    if re.search(r"^\d+ failed", out, re.M) or " failed" in out:
        return "assertion", (lines[-1][:300] if lines else "")
    return "other", (lines[-1][:300] if lines else "")


def diagnose(task_id: str, seed: int = 0) -> dict:
    from harness.run_all import setup_run
    from harness.reference_apply import build_reference_workspace

    task_dir = os.path.join(REPO_ROOT, "tasks", task_id)
    runs = tempfile.mkdtemp(prefix="g3diag_", dir="/tmp")
    rec: dict = {"task_id": task_id}
    try:
        _rid, run_dir, td = setup_run(task_id, os.path.join(REPO_ROOT, "tasks"),
                                      runs, seed=seed)
        ws = os.path.join(run_dir, "workspace")
        appl = build_reference_workspace(task_id, td, ws, seed=seed)
        rec["applied"] = appl["applied"]
        rec["method"] = appl["method"]
        rec["written_paths"] = appl.get("written_paths")
        tests, srcs = grader_targets(task_dir)
        rec["c1_targets"], rec["c5_targets"] = tests, srcs
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        if tests and tests[0].startswith("<whole workspace"):
            rec["c1_no_target"] = True
            tests = []
            r = subprocess.run([sys.executable, "-m", "pytest",
                                "-x", "-q", "--tb=short"], cwd=ws, env=env,
                               capture_output=True, text=True, errors="replace",
                               timeout=300)
            out = (r.stdout or "") + (r.stderr or "")
            rec["c1_rc"] = r.returncode
            rec["c1_cause"], rec["c1_evidence"] = classify(out)
            rec["c1_tail"] = out[-1200:]
        elif tests:
            r = subprocess.run([sys.executable, "-m", "pytest", *tests,
                                "-x", "-q", "--tb=short"], cwd=ws, env=env,
                               capture_output=True, text=True, errors="replace",
                               timeout=300)
            out = (r.stdout or "") + (r.stderr or "")
            rec["c1_rc"] = r.returncode
            rec["c1_cause"], rec["c1_evidence"] = classify(out)
            rec["c1_tail"] = out[-1200:]
        if srcs:
            causes = []
            for s in srcs:
                p = os.path.join(ws, s)
                if not os.path.isfile(p):
                    causes.append(("missing_target", s))
                    continue
                code = ("import importlib.util,sys\n"
                        "spec=importlib.util.spec_from_file_location('mod',sys.argv[1])\n"
                        "mod=importlib.util.module_from_spec(spec)\n"
                        "spec.loader.exec_module(mod)\n")
                r = subprocess.run([sys.executable, "-c", code, s], cwd=ws, env=env,
                                   capture_output=True, text=True, errors="replace",
                                   timeout=300)
                if r.returncode == 0:
                    causes.append(("ok", s))
                else:
                    causes.append(classify((r.stdout or "") + (r.stderr or "")))
                    rec.setdefault("c5_tail", (r.stdout or "") + (r.stderr or ""))
            rec["c5_causes"] = causes
    except Exception as exc:
        rec["error"] = f"{type(exc).__name__}: {exc}"[:300]
    finally:
        shutil.rmtree(runs, ignore_errors=True)
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks", nargs="*")
    ap.add_argument("--from-ledger", type=int, default=0,
                    help="Take the first N bucket-(b) tasks from the G3 checkpoint.")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(QUALITY, "g3_failure_diagnosis.json"))
    args = ap.parse_args()

    tasks = list(args.tasks)
    if args.from_ledger:
        ck = os.path.join(QUALITY, "g3_reference_checkpoint.jsonl")
        seen = []
        with open(ck, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("outcome") == "b_grader_rejects_reference":
                    seen.append(r["task_id"])
        tasks += seen[:args.from_ledger]
    tasks = list(dict.fromkeys(tasks))

    out = []
    for t in tasks:
        rec = diagnose(t, args.seed)
        out.append(rec)
        print(f"{t:34s} C1={rec.get('c1_cause')} "
              f"C5={[c for c, _ in rec.get('c5_causes', [])]}", flush=True)
    from collections import Counter
    c1 = Counter(r.get("c1_cause") for r in out if r.get("c1_cause"))
    c5 = Counter(c for r in out for c, _ in r.get("c5_causes", []))
    print("\nC1 causes:", c1.most_common())
    print("C5 causes:", c5.most_common())
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"summary": {"c1_causes": dict(c1), "c5_causes": dict(c5),
                               "n": len(out)}, "tasks": out}, f, indent=2)
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
