#!/usr/bin/env python3
"""Why did 12,161 of the stored runs fall out of the discriminative rescore?

The rescore needs two things per run: a checklist inside score.json, and a task
id recoverable so the pristine baseline can be looked up. This splits the misses
by which of the two was missing, because the remedies differ completely. A
missing checklist is a grader that never emitted one, which is a corpus defect.
An unresolvable task id is a path-parsing gap in the rescorer, which is our bug
and is fixable without rerunning anything.

Uses os.walk rather than glob('shared/**') because the tree is ~89 GB on NFS and
the recursive glob materialises the whole file list before yielding.
"""
from __future__ import annotations

import collections
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = os.path.join(REPO, "shared", "paper", "quality")


def main() -> int:
    os.chdir(REPO)
    base = json.load(open(os.path.join(Q, "pristine_checks.json")))
    base_lower = {k.lower(): k for k in base}

    reasons = collections.Counter()
    examples = collections.defaultdict(list)
    task_miss = collections.Counter()
    n = 0

    for root, _dirs, files in os.walk("shared"):
        if "score.json" not in files:
            continue
        sp = os.path.join(root, "score.json")
        n += 1
        try:
            sc = json.load(open(sp))
        except Exception:
            reasons["unreadable"] += 1
            continue
        sec = sc.get("secondary") or {}
        checks = sec.get("checks") or sc.get("checklist") or []
        parts = sp.split(os.sep)
        task = next((p for p in parts if p in base), None)
        # second chance: score.json usually names its own task, and the rescorer
        # never looked at that field
        named = sc.get("task_id") or sc.get("task")
        if not task and named:
            task = base_lower.get(str(named).lower())
        if task and checks:
            reasons["OK"] += 1
            continue
        if not checks and not task:
            r = "no_checklist_AND_no_task"
        elif not checks:
            r = "task_ok_but_no_checklist"
        else:
            r = "checklist_ok_but_task_unresolved"
            task_miss[str(named or (parts[2] if len(parts) > 2 else "?"))[:40]] += 1
        reasons[r] += 1
        if len(examples[r]) < 4:
            examples[r].append(sp)
        if n % 4000 == 0:
            print(f"  scanned {n}", flush=True)

    print(f"\nscore.json files: {n}\n")
    for k, v in reasons.most_common():
        print(f"  {k:38} {v:6}  {100*v/max(1,n):5.1f}%")
    print("\nexamples:")
    for r, ex in examples.items():
        print(f"  {r}:")
        for e in ex[:3]:
            print(f"     {e}")
    if task_miss:
        print("\ntask ids in a checklist but absent from the baseline:")
        for k, v in task_miss.most_common(12):
            print(f"   {v:5}  {k}")
    json.dump({"n": n, "reasons": dict(reasons), "task_miss": dict(task_miss)},
              open(os.path.join(Q, "rescore_skip_diagnosis.json"), "w"), indent=1)
    print(f"\nwrote {os.path.join(Q, 'rescore_skip_diagnosis.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
