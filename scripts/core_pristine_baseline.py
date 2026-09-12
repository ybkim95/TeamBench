#!/usr/bin/env python3
"""Recompute the do-nothing baseline on STAGED core tasks.

shared/paper/quality/pristine_checks.json was measured against the old vendored
workspaces, which held only the files a pull request touched. Every core task is
now checked out from upstream at base_sha and has the pull request's tests
injected at grade time, so that baseline is stale for all 48 of them.

What the baseline is for: a check counts as DISCRIMINATIVE for a task iff it
fails when nothing has been done. Everything else is a guard ("source still
parses", "tests not deleted", "file has at least N lines") that sits in both the
numerator and the denominator of partial_score and pays a submission for not
vandalising the workspace. That is a per-(task, check) property and never a
property of the check's name: "source modules import without error" is a guard
on one task and the entire point of another.

This runs the real runtime path, harness.run_all.setup_run + grade_run, rather
than reimplementing it, so the baseline is exactly what the benchmark produces:
setup_run stages from upstream for a core task, grade_run restores the held-out
tests before grading.

The submission is empty apart from a passing attestation, which is deliberate.
The attestation gate is a separate control; leaving it unsatisfied would mask
the task score and make every check look discriminative.

Usage:
  python scripts/core_pristine_baseline.py --workers 4
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
Q = os.path.join(REPO, "shared", "paper", "quality")
OUT = os.path.join(Q, "pristine_checks_core.json")


def check_key(c: dict) -> str:
    """Stable identity for a check within a task, matching discriminative_rescore."""
    return str(c.get("id") or "") + "|" + str(c.get("note") or "")[:80]


def one(task: str, runs_root: str, timeout: int) -> dict:
    from harness.run_all import setup_run, grade_run
    run_dir = None
    try:
        run_id, run_dir, task_dir = setup_run(task, os.path.join(REPO, "tasks"),
                                              runs_root, seed=0)
        sub = os.path.join(run_dir, "submission")
        os.makedirs(sub, exist_ok=True)
        json.dump({"task_id": task, "verdict": "pass", "checklist": []},
                  open(os.path.join(sub, "attestation.json"), "w"))
        sc = grade_run(task, task_dir, run_dir)
        sec = sc.get("secondary") or {}
        checks = sec.get("checks") or sc.get("checklist") or []
        if not checks:
            return {"task": task, "status": "no_checklist"}
        allk = [check_key(c) for c in checks if isinstance(c, dict)]
        free = [check_key(c) for c in checks if isinstance(c, dict) and c.get("ok")]
        return {"task": task, "status": "ok",
                "all": allk, "free": free,
                "pristine_partial": sec.get("partial_score"),
                "pristine_pass": bool(sc.get("pass")),
                "n_discriminative": len(allk) - len(free)}
    except Exception as e:
        return {"task": task, "status": "error", "err": str(e)[:200]}
    finally:
        if run_dir:
            shutil.rmtree(os.path.dirname(run_dir), ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--tasks-file",
                    default=os.path.join(Q, "core_tasks.json"))
    a = ap.parse_args()

    sel = json.load(open(a.tasks_file))
    tasks = sel["selected_flat"] if isinstance(sel, dict) else sel
    print("core tasks to baseline: %d  (workers=%d)" % (len(tasks), a.workers),
          flush=True)

    runs_root = tempfile.mkdtemp(prefix="baseline_")
    rows = []
    try:
        with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
            futs = {ex.submit(one, t, runs_root, a.timeout): t for t in tasks}
            for i, f in enumerate(cf.as_completed(futs), 1):
                rows.append(f.result())
                if i % 5 == 0 or i == len(tasks):
                    print("  [%d/%d]" % (i, len(tasks)), flush=True)
    finally:
        shutil.rmtree(runs_root, ignore_errors=True)

    ok = [r for r in rows if r.get("status") == "ok"]
    base = {r["task"]: {"all": r["all"], "free": r["free"],
                        "pristine_partial": r["pristine_partial"]} for r in ok}
    json.dump(base, open(OUT, "w"), indent=1)
    json.dump(rows, open(OUT.replace(".json", "_detail.json"), "w"), indent=1)

    import statistics
    parts = [r["pristine_partial"] for r in ok
             if isinstance(r["pristine_partial"], (int, float))]
    nod = [r for r in ok if r["n_discriminative"] == 0]
    passed = [r for r in ok if r.get("pristine_pass")]
    print("\nbaselined %d of %d" % (len(ok), len(rows)))
    if parts:
        print("  mean do-nothing partial on the OLD scale : %.3f" % statistics.mean(parts))
    print("  tasks an empty submission already PASSES    : %d  <- must be 0" % len(passed))
    print("  tasks with NO discriminative check          : %d  <- must be 0" % len(nod))
    for r in nod[:5]:
        print("      %s" % r["task"])
    print("\nwrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
