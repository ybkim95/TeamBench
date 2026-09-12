#!/usr/bin/env python3
"""Select 25 tasks pro-rata from leaderboard_100_tasks.json for role ablation.

Uses Hamilton's largest-remainder method to apportion 25 seats across
categories. Within-category tie-break: hardest difficulty first, then
deterministic alphabetical by task_id.

Usage:
    python scripts/select_role_ablation_tasks.py
    python scripts/select_role_ablation_tasks.py --n 25 --output shared/role_ablation/tasks_25.json
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LB100 = REPO_ROOT / "leaderboard" / "data" / "leaderboard_100_tasks.json"
DEFAULT_OUT = REPO_ROOT / "shared" / "role_ablation" / "tasks_25.json"

DIFFICULTY_RANK = {"expert": 0, "hard": 1, "medium": 2, "easy": 3}


def hamilton_apportion(counts: dict[str, int], total: int) -> dict[str, int]:
    """Hamilton's largest-remainder apportionment."""
    grand = sum(counts.values())
    assert grand > 0, "empty counts"
    exact = {k: v * total / grand for k, v in counts.items()}
    base = {k: int(v) for k, v in exact.items()}
    remainder = {k: exact[k] - base[k] for k in counts}
    leftover = total - sum(base.values())
    # Sort by remainder desc, tie-break by category name for determinism
    ordered = sorted(remainder.items(), key=lambda kv: (-kv[1], kv[0]))
    for k, _ in ordered[:leftover]:
        base[k] += 1
    return base


def pick_within(tasks: list[dict], k: int) -> list[dict]:
    """Pick k tasks from a category list. Hardest first, then task_id alphabetical."""
    ordered = sorted(
        tasks,
        key=lambda t: (DIFFICULTY_RANK.get(t.get("difficulty", "medium"), 2), t["task_id"]),
    )
    return ordered[:k]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=25)
    ap.add_argument("--source", type=Path, default=LB100)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    with open(args.source) as f:
        lb = json.load(f)
    tasks = lb["tasks"]
    assert len(tasks) == 100, f"expected 100 tasks, got {len(tasks)}"

    by_cat: dict[str, list[dict]] = defaultdict(list)
    for t in tasks:
        by_cat[t["category"]].append(t)

    counts = {c: len(ts) for c, ts in by_cat.items()}
    quotas = hamilton_apportion(counts, args.n)

    selected: list[dict] = []
    quota_report = []
    for cat in sorted(by_cat.keys()):
        q = quotas[cat]
        picks = pick_within(by_cat[cat], q)
        selected.extend(picks)
        quota_report.append({
            "category": cat,
            "available": counts[cat],
            "quota": q,
            "selected": [p["task_id"] for p in picks],
        })

    assert len(selected) == args.n, f"got {len(selected)}, expected {args.n}"

    out = {
        "version": "1.0",
        "n": args.n,
        "source": str(args.source.relative_to(REPO_ROOT)),
        "method": "hamilton_largest_remainder",
        "tie_break": "difficulty_rank_asc, task_id_asc",
        "tasks": [
            {
                "task_id": t["task_id"],
                "category": t["category"],
                "difficulty": t.get("difficulty", "unknown"),
            }
            for t in selected
        ],
        "quota_report": quota_report,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(out, f, indent=2)

    print(f"Wrote {args.output} with {args.n} tasks across {len(quotas)} categories.")
    print("\nPer-category quotas:")
    for r in quota_report:
        marker = "✓" if r["quota"] > 0 else " "
        print(f"  {marker} {r['category']:<30} {r['available']:>3} → {r['quota']}")
    print("\nSelected task IDs:")
    for i, t in enumerate(selected, 1):
        print(f"  {i:>2}. {t['task_id']:<40} [{t['category']}, {t.get('difficulty','?')}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
