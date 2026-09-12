#!/usr/bin/env python3
"""Re-grade grader_no_score runs in any lb100_*.checkpoint.jsonl file.

The original grader timeout (600s) sometimes fires under load even when the
workspace is correct. Re-run grade_run on the preserved run_dir to recover
the score. Writes a backup of the input file before mutating.

Usage:
    python scripts/regrade_lb100_checkpoint.py <checkpoint.jsonl> [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from harness.run_all import grade_run

TASKS_DIR = REPO_ROOT / "tasks"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint", help="Path to lb100_*.checkpoint.jsonl")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ckpt = Path(args.checkpoint).resolve()
    rows = [json.loads(line) for line in ckpt.open() if line.strip()]

    candidates = [
        (i, r) for i, r in enumerate(rows)
        if "grader_no_score" in (r.get("failure_modes") or [])
    ]
    print(f"Found {len(candidates)} grader_no_score runs of {len(rows)} total.")
    if not candidates:
        return 0

    if not args.dry_run:
        backup = str(ckpt) + ".pre_regrade_backup"
        shutil.copy2(ckpt, backup)
        print(f"Backup written: {backup}")

    recovered_pass = 0
    recovered_partial = 0
    still_no_score = 0
    skipped = 0
    for i, r in candidates:
        run_dir = r.get("run_dir", "")
        task_id = r["task_id"]
        task_dir = str(TASKS_DIR / task_id)
        if not run_dir or not os.path.isdir(run_dir):
            skipped += 1
            continue
        if args.dry_run:
            print(f"  [dry] {r['condition']} x {task_id}")
            continue

        score = grade_run(task_id, task_dir, run_dir)
        passed = bool(score.get("pass", False))
        partial = float(score.get("secondary", {}).get(
            "partial_score", 1.0 if passed else 0.0
        ))
        new_fm = score.get("failure_modes", [])
        before_fm = r.get("failure_modes", [])
        r["pass"] = passed
        r["partial_score"] = partial
        r["failure_modes"] = new_fm
        r["regraded"] = True

        tag = "PASS" if passed else f"partial={partial:.2f}"
        marker = ""
        if "grader_no_score" in new_fm:
            still_no_score += 1
            marker = " (still GNS)"
        elif passed:
            recovered_pass += 1
        elif partial > 0:
            recovered_partial += 1
        print(f"  [regrade] {r['condition']:18s} x {task_id:35s} → {tag}{marker}")

    if args.dry_run:
        return 0

    tmp = str(ckpt) + ".tmp"
    with open(tmp, "w") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    os.replace(tmp, ckpt)
    print()
    print(f"Recovered passes:        {recovered_pass}")
    print(f"Recovered partial >0:    {recovered_partial}")
    print(f"Still grader_no_score:   {still_no_score}")
    print(f"Skipped (no run_dir):    {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
