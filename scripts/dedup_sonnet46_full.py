#!/usr/bin/env python3
"""Dedup sonnet46's 4 full-resume checkpoint files into a single canonical entry per task.

Selection rule per (task_id, seed) for the 'full' condition:
  1. Prefer entries with pass=True
  2. Then prefer no error AND no grader_no_score
  3. Then highest partial_score
  4. Tiebreak by latest run_id

Backups every input checkpoint, then merges into the oraclefull checkpoint.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path("/u/ybkim95/TeamBench/shared/ablation_results")
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
SUFFIX = f".pre_dedup_sonnet46_{TS}"

INPUTS = [
    "lb100_sonnet46_oraclefull_seed0.json.checkpoint.jsonl",
    "lb100_sonnet46_full_resume.json.checkpoint.jsonl",
    "lb100_sonnet46_full_resume2.json.checkpoint.jsonl",
    "lb100_sonnet46_full_resume3.json.checkpoint.jsonl",
]
CANONICAL = ROOT / INPUTS[0]


def quality(entry: dict) -> tuple:
    fm = entry.get("failure_modes") or []
    is_pass = bool(entry.get("pass"))
    has_error = bool(entry.get("error"))
    is_gns = "grader_no_score" in fm
    partial = float(entry.get("partial_score") or 0.0)
    run_id = entry.get("run_id") or ""
    # Higher tuple wins
    return (
        int(is_pass),
        int(not has_error),
        int(not is_gns),
        partial,
        run_id,
    )


def main() -> int:
    # Load all entries
    all_runs: list[dict] = []
    for name in INPUTS:
        p = ROOT / name
        if not p.is_file():
            print(f"  [skip] {name} (not found)")
            continue
        with p.open() as f:
            for line in f:
                if line.strip():
                    all_runs.append(json.loads(line))
        # Backup
        shutil.copy2(p, str(p) + SUFFIX)

    print(f"Loaded {len(all_runs)} entries from {len(INPUTS)} files")

    # Group by (condition, task_id, seed)
    best: dict[tuple, dict] = {}
    full_seen: set[tuple] = set()
    for r in all_runs:
        key = (r.get("condition"), r.get("task_id"), r.get("seed"))
        if key not in best or quality(r) > quality(best[key]):
            best[key] = r
        if r.get("condition") == "full":
            full_seen.add(r.get("task_id"))

    print(f"Deduped to {len(best)} entries")
    print(f"  full conditions: {sum(1 for k in best if k[0]=='full')}/100 unique tasks")
    print(f"  oracle conditions: {sum(1 for k in best if k[0]=='oracle')}/100 unique tasks")

    # Write the deduped canonical checkpoint
    tmp = str(CANONICAL) + ".tmp"
    with open(tmp, "w") as f:
        for r in best.values():
            f.write(json.dumps(r) + "\n")
    Path(tmp).replace(CANONICAL)
    print(f"Wrote {CANONICAL}")

    # Rename non-canonical inputs so they don't get re-merged on re-run
    for name in INPUTS[1:]:
        p = ROOT / name
        if p.is_file():
            new = str(p) + ".consolidated_into_canonical"
            shutil.move(str(p), new)
            print(f"Archived: {name} -> {Path(new).name}")
        # Also rename the corresponding final JSON if present
        final = ROOT / name.replace(".checkpoint.jsonl", "")
        if final.is_file():
            new = str(final) + ".consolidated_into_canonical"
            shutil.move(str(final), new)
            print(f"Archived: {final.name} -> {Path(new).name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
