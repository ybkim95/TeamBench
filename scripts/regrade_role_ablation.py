#!/usr/bin/env python3
"""Re-grade role_ablation runs with current graders.

Walks shared/role_ablation/results/per_run.jsonl, re-runs grade.sh on each
preserved run_dir, and APPENDS patch rows (same key, new pass/partial_score).
Aggregation (harness/ablation.py) keeps LAST entry per (config, task, seed)
key, so patches override originals.

Safe to run concurrently with run_role_ablation.py (appends are atomic for
small lines on Linux).
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
os.chdir(REPO)

from harness.run_all import grade_run

PER_RUN = REPO / "shared/role_ablation/results/per_run.jsonl"
TASKS_DIR = REPO / "tasks"


def _load_latest() -> list[dict]:
    """Load last-wins rows from per_run.jsonl, so we regrade current state."""
    latest: dict[tuple, dict] = {}
    with open(PER_RUN) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = (r["config"], r["task_id"], int(r.get("seed", 0)))
            latest[key] = r
    return list(latest.values())


def _regrade_one(row: dict) -> tuple[str, dict, dict | str | None]:
    rd = row.get("run_dir")
    tid = row.get("task_id")
    if not rd or not os.path.isdir(rd):
        return ("missing", row, None)
    task_dir = TASKS_DIR / tid
    if not task_dir.is_dir():
        return ("no_task", row, None)
    try:
        res = grade_run(tid, str(task_dir), rd)
        return ("ok", row, res)
    except Exception as e:  # noqa: BLE001
        return ("err", row, str(e))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--parallel", type=int, default=16)
    ap.add_argument("--only-changed", action="store_true",
                    help="Only append patch if pass or partial_score changed")
    ap.add_argument("--seeds", type=str, default="0",
                    help="Comma-separated seeds to regrade (default: 0)")
    args = ap.parse_args()

    seeds_to_regrade = {int(s) for s in args.seeds.split(",")}

    rows = _load_latest()
    rows = [r for r in rows if int(r.get("seed", 0)) in seeds_to_regrade]
    print(f"Loaded {len(rows)} latest rows for seeds {sorted(seeds_to_regrade)}",
          flush=True)

    t0 = time.time()
    changed = unchanged = missing = errored = 0
    patches: list[dict] = []

    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futures = [pool.submit(_regrade_one, r) for r in rows]
        for i, fut in enumerate(as_completed(futures), 1):
            status, row, res = fut.result()
            if status == "missing":
                missing += 1
                continue
            if status == "no_task":
                errored += 1
                continue
            if status == "err":
                errored += 1
                print(f"  [err] {row['config']} × {row['task_id']} "
                      f"seed={row['seed']}: {res}", flush=True)
                continue
            new_pass = bool(res.get("pass", False))
            # Match run_role_ablation.py extraction: partial_score lives under
            # secondary; fall back to 1.0/0.0 based on pass for graders that
            # omit it.
            new_partial = float(
                res.get("secondary", {}).get(
                    "partial_score", 1.0 if new_pass else 0.0,
                )
            )
            old_pass = bool(row.get("pass", False))
            old_partial = float(row.get("partial_score", 0.0))
            same = (new_pass == old_pass) and (abs(new_partial - old_partial) < 1e-9)
            if same:
                unchanged += 1
                if args.only_changed:
                    continue
            else:
                changed += 1
                print(f"  [diff] {row['config']:<8} × {row['task_id']:<32} "
                      f"seed={row['seed']} "
                      f"pass {old_pass}->{new_pass} "
                      f"partial {old_partial:.2f}->{new_partial:.2f}",
                      flush=True)
            patch = dict(row)
            patch["pass"] = new_pass
            patch["partial_score"] = new_partial
            patch["regraded_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                 time.gmtime())
            patches.append(patch)
            if i % 50 == 0:
                elapsed = time.time() - t0
                print(f"  [{i}/{len(rows)}] elapsed={elapsed:.0f}s "
                      f"changed={changed} unchanged={unchanged}",
                      flush=True)

    dt = time.time() - t0
    print(f"\nDone in {dt:.0f}s. changed={changed} unchanged={unchanged} "
          f"missing={missing} errored={errored}", flush=True)

    if args.dry_run:
        print("[dry-run] not writing patches.")
        return 0

    if patches:
        with open(PER_RUN, "a") as f:
            for p in patches:
                f.write(json.dumps(p) + "\n")
        print(f"Appended {len(patches)} patch rows to {PER_RUN}", flush=True)
    else:
        print("No patches to append.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
