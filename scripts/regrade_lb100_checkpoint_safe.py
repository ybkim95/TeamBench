#!/usr/bin/env python3
"""Race-safe regrade for grader_no_score runs in active lb100 checkpoints.

Unlike `regrade_lb100_checkpoint.py` which rewrites the whole file (and would
silently drop any line appended by a live runner during the rewrite), this
version APPENDS a patch entry per regraded run. Aggregation logic must dedupe
by (condition, task_id, seed) and keep the LAST entry per key (the patch).

POSIX append writes under PIPE_BUF (~4KB) are atomic, so concurrent appends
from the live runner do not interleave with ours.

Usage:
    python scripts/regrade_lb100_checkpoint_safe.py <checkpoint.jsonl> [--dry-run] [--limit N]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from harness.run_all import grade_run

TASKS_DIR = REPO_ROOT / "tasks"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint", help="Path to lb100_*.checkpoint.jsonl")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="Max entries to regrade (0=all)")
    ap.add_argument("--min-age-sec", type=int, default=120,
                    help="Skip entries with run_id newer than this many seconds (avoid live races)")
    args = ap.parse_args()

    ckpt = Path(args.checkpoint).resolve()
    if not ckpt.is_file():
        print(f"  [error] not a file: {ckpt}", file=sys.stderr)
        return 2

    rows = [json.loads(line) for line in ckpt.open() if line.strip()]
    # Take the LAST entry per (condition, task_id, seed) — that's the current state
    by_key: dict[tuple, dict] = {}
    for r in rows:
        key = (r.get("condition"), r.get("task_id"), r.get("seed"))
        by_key[key] = r

    candidates: list[dict] = []
    now = time.time()
    skipped_recent = 0
    for r in by_key.values():
        if "grader_no_score" not in (r.get("failure_modes") or []):
            continue
        if not r.get("run_dir") or not os.path.isdir(r["run_dir"]):
            continue
        # Skip recent runs to avoid racing the live runner
        run_id = r.get("run_id", "")
        if run_id:
            try:
                ts = datetime.strptime(run_id.split("_")[0] + "_" + run_id.split("_")[1],
                                       "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc).timestamp()
                if now - ts < args.min_age_sec:
                    skipped_recent += 1
                    continue
            except (ValueError, IndexError):
                pass
        candidates.append(r)

    if args.limit:
        candidates = candidates[: args.limit]

    print(f"Found {len(candidates)} regradeable GNS entries (current state).")
    print(f"Skipped {skipped_recent} too-recent entries (< {args.min_age_sec}s old).")

    if not candidates or args.dry_run:
        for r in candidates[:5]:
            print(f"  [dry] {r['condition']} x {r['task_id']}")
        if len(candidates) > 5:
            print(f"  ... and {len(candidates) - 5} more")
        return 0

    recovered_pass = 0
    recovered_partial = 0
    still_no_score = 0
    appended = 0

    # Open in append mode — POSIX guarantees atomicity for writes < PIPE_BUF
    with ckpt.open("a") as out:
        for r in candidates:
            task_id = r["task_id"]
            task_dir = str(TASKS_DIR / task_id)
            score = grade_run(task_id, task_dir, r["run_dir"])
            passed = bool(score.get("pass", False))
            partial = float(score.get("secondary", {}).get(
                "partial_score", 1.0 if passed else 0.0
            ))
            new_fm = score.get("failure_modes", [])

            patch = dict(r)  # copy
            patch["pass"] = passed
            patch["partial_score"] = partial
            patch["failure_modes"] = new_fm
            patch["regraded"] = True
            patch["regraded_at"] = datetime.now(timezone.utc).isoformat()

            line = json.dumps(patch, default=str) + "\n"
            if len(line) >= 3500:
                # Stay well under PIPE_BUF (4096) for append atomicity
                # Drop any oversized fields if needed
                patch2 = {k: v for k, v in patch.items() if k != "score"}
                line = json.dumps(patch2, default=str) + "\n"
            out.write(line)
            out.flush()
            appended += 1

            tag = "PASS" if passed else f"partial={partial:.2f}"
            marker = " (still GNS)" if "grader_no_score" in new_fm else ""
            if "grader_no_score" in new_fm:
                still_no_score += 1
            elif passed:
                recovered_pass += 1
            elif partial > 0:
                recovered_partial += 1
            print(f"  [regrade] {r['condition']:18s} x {task_id:35s} → {tag}{marker}")

    print()
    print(f"Appended patches:        {appended}")
    print(f"Recovered passes:        {recovered_pass}")
    print(f"Recovered partial >0:    {recovered_partial}")
    print(f"Still grader_no_score:   {still_no_score}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
