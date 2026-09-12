#!/usr/bin/env python3
"""Re-grade any runs in per_run.jsonl that have failure_modes=['grader_no_score'].

Use after a campaign finishes (or any time) to fix cases where the grader
timed out during the live run but the workspace is actually correct. The
grader subprocess timeout was raised to 600s in run_all.py.

Usage:
    python scripts/regrade_grader_no_score.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from harness.run_all import grade_run

PER_RUN = REPO_ROOT / "shared" / "role_ablation" / "results" / "per_run.jsonl"
TASKS_DIR = REPO_ROOT / "tasks"
PRICING = REPO_ROOT / "shared" / "role_ablation" / "pricing.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = []
    with open(PER_RUN) as f:
        for line in f:
            rows.append(json.loads(line))

    candidates = [
        (i, r) for i, r in enumerate(rows)
        if "grader_no_score" in (r.get("failure_modes") or [])
    ]
    print(f"Found {len(candidates)} runs with grader_no_score (of {len(rows)} total).")
    if not candidates:
        return 0

    updated = 0
    for i, r in candidates:
        run_dir = r.get("run_dir", "")
        task_id = r["task_id"]
        task_dir = str(TASKS_DIR / task_id)
        if not run_dir or not os.path.isdir(run_dir):
            print(f"  [skip] {r['config']} × {task_id}: run_dir missing")
            continue
        print(f"  [regrade] {r['config']} × {task_id} ...", end="", flush=True)
        if args.dry_run:
            print(" DRY-RUN")
            continue
        score = grade_run(task_id, task_dir, run_dir)
        passed = bool(score.get("pass", False))
        partial = float(score.get("secondary", {}).get(
            "partial_score", 1.0 if passed else 0.0
        ))
        r["pass"] = passed
        r["partial_score"] = partial
        r["failure_modes"] = score.get("failure_modes", [])
        r["regraded"] = True
        print(f" pass={passed} partial={partial:.2f}")
        updated += 1

    if not args.dry_run and updated:
        tmp = str(PER_RUN) + ".tmp"
        with open(tmp, "w") as f:
            for r in rows:
                f.write(json.dumps(r, default=str) + "\n")
        os.replace(tmp, PER_RUN)
        print(f"Updated {updated} rows in {PER_RUN}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
