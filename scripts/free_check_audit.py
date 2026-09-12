#!/usr/bin/env python3
"""Which individual checks award credit for doing nothing?

The admission gate's G1 (pristine floor must be 0) fails on 230 of 240 tasks, and
the mean floor is 0.551. That single number is what blocks every other gate from
mattering, but it does not say WHICH checks are responsible, so it cannot be acted
on. This grades pristine workspaces and tabulates the per-check outcome, grouped
by a normalised form of the check's own description.

The output splits checks into:

  GATING        passes on an untouched workspace by design. These are guards
                against vandalism (source still parses, tests not deleted), not
                measurements of the submission. They belong in a pass/fail
                admissibility test, not in the score.
  DISCRIMINATIVE fails on the untouched workspace, so solving the task is what
                makes it pass. These are the checks that should carry the score.

The remedy this measurement supports is to score only the discriminative set and
report the gating set separately, which drops the floor toward 0 without weakening
any anti-cheat guarantee.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS = os.path.join(REPO, "tasks")


def norm(note: str) -> str:
    n = (note or "").lower().strip()
    n = re.sub(r"[\"'`]", "", n)
    n = re.sub(r"\b\d+\b", "N", n)
    n = re.sub(r"\s+", " ", n)
    return n[:60]


def grade_pristine(task: str, timeout: int):
    ws_src = os.path.join(TASKS, task, "workspace")
    if not os.path.isdir(ws_src) or not os.listdir(ws_src):
        return None
    run = tempfile.mkdtemp(prefix="fca_")
    try:
        ws = os.path.join(run, "workspace")
        shutil.copytree(ws_src, ws)
        for d in ("reports", "submission"):
            os.makedirs(os.path.join(run, d))
        json.dump({"task_id": task, "verdict": "pass", "checklist": []},
                  open(os.path.join(run, "submission", "attestation.json"), "w"))
        try:
            subprocess.run(["bash", os.path.join(TASKS, task, "grade.sh"), ws,
                            os.path.join(run, "reports"), os.path.join(run, "submission"),
                            os.path.join(TASKS, task)],
                           capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return None
        p = os.path.join(run, "reports", "score.json")
        if not os.path.isfile(p):
            return None
        return json.load(open(p))
    finally:
        shutil.rmtree(run, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--timeout", type=int, default=90)
    ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--out", default="shared/paper/quality/free_check_audit.json")
    a = ap.parse_args()

    cands = [d for d in sorted(os.listdir(TASKS))
             if os.path.isfile(os.path.join(TASKS, d, "grade.sh"))
             and os.path.isdir(os.path.join(TASKS, d, "workspace"))
             and os.listdir(os.path.join(TASKS, d, "workspace"))]
    sample = random.Random(a.seed).sample(cands, min(a.n, len(cands)))
    print(f"tasks with a static workspace: {len(cands)}; grading {len(sample)}", flush=True)

    passes, total = collections.Counter(), collections.Counter()
    per_task, graded = [], 0
    for i, t in enumerate(sample, 1):
        sc = grade_pristine(t, a.timeout)
        if not sc:
            continue
        graded += 1
        sec = sc.get("secondary") or {}
        checks = sec.get("checks") or sc.get("checklist") or []
        got = 0
        for c in checks:
            if not isinstance(c, dict):
                continue
            k = norm(c.get("note") or c.get("id") or "")
            total[k] += 1
            if c.get("ok"):
                passes[k] += 1
                got += 1
        per_task.append({"task": t, "partial": sec.get("partial_score"),
                         "checks": len(checks), "free": got})
        if i % 25 == 0:
            print(f"  {i}/{len(sample)} graded={graded}", flush=True)

    rows = []
    for k, n in total.most_common():
        f = passes[k]
        rows.append({"check": k, "n": n, "free": f, "free_rate": f / n,
                     "class": "GATING" if f / n >= 0.9 else
                              "DISCRIMINATIVE" if f / n <= 0.2 else "MIXED"})
    out = {"graded_tasks": graded, "checks": rows, "per_task": per_task}
    os.makedirs(os.path.dirname(os.path.join(REPO, a.out)), exist_ok=True)
    json.dump(out, open(os.path.join(REPO, a.out), "w"), indent=1)

    tot_checks = sum(r["n"] for r in rows)
    tot_free = sum(r["free"] for r in rows)
    print(f"\ngraded {graded} tasks, {tot_checks} checks, "
          f"{tot_free} pass on an untouched workspace ({100*tot_free/max(1,tot_checks):.1f}%)\n")
    print(f"{'check':62} {'n':>4} {'free':>6} {'class':>15}")
    print("-" * 92)
    for r in rows[:22]:
        print(f"  {r['check']:60} {r['n']:>4} {100*r['free_rate']:>5.0f}% {r['class']:>15}")
    by = collections.Counter(r["class"] for r in rows)
    fb = collections.Counter()
    for r in rows:
        fb[r["class"]] += r["free"]
    print("-" * 92)
    print("  class          distinct checks   free credit awarded")
    for c in ("GATING", "MIXED", "DISCRIMINATIVE"):
        print(f"  {c:15} {by.get(c,0):>13} {fb.get(c,0):>21}")
    print(f"\n  removing GATING checks from the score would remove "
          f"{fb.get('GATING',0)}/{tot_free} of all free credit")
    print(f"\nwrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
