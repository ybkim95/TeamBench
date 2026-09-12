#!/usr/bin/env python3
"""Strip entries for a given condition from one or more lb100 checkpoint files.

Used after fixing a bug in a specific ablation condition (e.g. the restricted
attestation-path bug). Backs up each checkpoint with a timestamp suffix before
mutating, then re-writes the JSONL with the named condition removed.

Usage:
    python scripts/strip_condition_from_checkpoint.py \\
        --condition restricted \\
        --reason restricted_path_bug_fix \\
        shared/ablation_results/lb100_haiku45_3cond_seed0.json.checkpoint.jsonl ...
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True, help="Condition to strip, e.g. 'restricted'")
    ap.add_argument("--reason", default="strip", help="Tag included in backup suffix")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("checkpoints", nargs="+", help="Checkpoint .jsonl files")
    args = ap.parse_args()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f".pre_{args.reason}_{ts}"

    for path_str in args.checkpoints:
        ckpt = Path(path_str).resolve()
        if not ckpt.is_file():
            print(f"  [skip] not a file: {ckpt}")
            continue

        rows = [json.loads(line) for line in ckpt.open() if line.strip()]
        keep = [r for r in rows if r.get("condition") != args.condition]
        stripped = len(rows) - len(keep)
        if stripped == 0:
            print(f"  [no-op] {ckpt.name}: no '{args.condition}' entries")
            continue

        if args.dry_run:
            print(f"  [dry] {ckpt.name}: would strip {stripped}/{len(rows)}")
            continue

        backup = str(ckpt) + suffix
        shutil.copy2(ckpt, backup)
        tmp = str(ckpt) + ".tmp"
        with open(tmp, "w") as f:
            for r in keep:
                f.write(json.dumps(r) + "\n")
        Path(tmp).replace(ckpt)
        print(f"  [ok] {ckpt.name}: stripped {stripped}/{len(rows)} (backup: {Path(backup).name})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
