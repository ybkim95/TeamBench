#!/usr/bin/env python3
"""
Select 100 tasks uniformly across all categories for the expanded leaderboard.

Usage:
    python scripts/select_leaderboard_100.py
"""

import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DATASET_PATH = REPO_ROOT / "shared" / "teambench_dataset.json"
ABLATION_DIR = REPO_ROOT / "shared" / "ablation_results"
OUTPUT_PATH = REPO_ROOT / "leaderboard" / "data" / "leaderboard_100_tasks.json"

SELECTION_DATE = "2026-04-10"
TARGET_N = 100
CAP_PER_CATEGORY = 30

DIFFICULTY_ORDER = {"expert": 0, "hard": 1, "medium": 2, "easy": 3}


# ---------------------------------------------------------------------------
# Sub-category classification for the "Other" bucket
# ---------------------------------------------------------------------------

def _gh_number(task_id: str) -> int | None:
    """Return the numeric part of a GH-prefixed task_id, or None."""
    m = re.match(r"^GH(\d+)", task_id)
    return int(m.group(1)) if m else None


def refined_category(task: dict) -> str:
    """Map a task to its refined category name."""
    cat = task["category"]
    tid = task["task_id"]
    if cat != "Other":
        return cat
    num = _gh_number(tid)
    if num is not None and num >= 1000:
        return "GitHub Issues (Real-World)"
    if tid.startswith("RDS"):
        return "Real Data Science"
    if tid.startswith("DS"):
        return "Data Science (Stat/ML)"
    return "Other (Misc)"


# ---------------------------------------------------------------------------
# Collect ablation task_ids
# ---------------------------------------------------------------------------

def load_ablation_task_ids() -> set[str]:
    """Return the set of task_ids that have any existing ablation scores."""
    seen: set[str] = set()
    if not ABLATION_DIR.exists():
        return seen
    for fpath in ABLATION_DIR.glob("*.json"):
        try:
            with open(fpath) as f:
                d = json.load(f)
        except Exception:
            continue
        # Various shapes used across ablation files
        if isinstance(d, dict):
            for run in d.get("runs", []):
                if isinstance(run, dict):
                    tid = run.get("task_id") or run.get("task")
                    if tid:
                        seen.add(tid)
            tasks_val = d.get("tasks", [])
            if not isinstance(tasks_val, list):
                tasks_val = []
            for t in tasks_val:
                if isinstance(t, str):
                    seen.add(t)
                elif isinstance(t, dict):
                    tid = t.get("task_id") or t.get("task")
                    if tid:
                        seen.add(tid)
        elif isinstance(d, list):
            for item in d:
                if isinstance(item, dict):
                    tid = item.get("task_id") or item.get("task")
                    if tid:
                        seen.add(tid)
    return seen


# ---------------------------------------------------------------------------
# Floor / quota computation
# ---------------------------------------------------------------------------

def floor_for_size(n: int) -> int:
    if n < 5:
        return min(2, n)
    if n < 10:
        return 3
    if n < 20:
        return 4
    return 5  # 20+


def compute_quotas(category_sizes: dict[str, int], target: int, cap: int) -> dict[str, int]:
    """
    1. Assign floors.
    2. Distribute remaining slots proportionally to category size, capped at `cap`.
    Returns quotas that sum to exactly `target`.
    """
    cats = list(category_sizes.keys())
    floors = {c: floor_for_size(category_sizes[c]) for c in cats}
    remaining = target - sum(floors.values())

    if remaining < 0:
        # Too many floors — scale down proportionally (shouldn't happen with 19+ cats)
        scale = target / sum(floors.values())
        quotas = {c: max(1, int(floors[c] * scale)) for c in cats}
        # Trim to exactly target
        diff = sum(quotas.values()) - target
        for c in sorted(cats, key=lambda x: -quotas[x]):
            if diff <= 0:
                break
            quotas[c] -= 1
            diff -= 1
        return quotas

    # Proportional distribution of remaining slots
    total_size = sum(category_sizes[c] for c in cats)
    extra: dict[str, float] = {
        c: remaining * category_sizes[c] / total_size for c in cats
    }
    # Integer parts + sort remainder
    quotas = {c: floors[c] + int(extra[c]) for c in cats}
    # Apply cap
    quotas = {c: min(quotas[c], cap) for c in cats}

    # Distribute any leftover slots (due to int truncation or cap)
    # Iterate by largest fractional part, respecting cap
    frac = {c: (extra[c] - int(extra[c])) for c in cats}
    allocated = sum(quotas.values())
    still_needed = target - allocated
    for c in sorted(cats, key=lambda x: -frac[x]):
        if still_needed <= 0:
            break
        if quotas[c] < cap and quotas[c] < category_sizes[c]:
            quotas[c] += 1
            still_needed -= 1

    # Edge case: if we're still short (all categories capped), relax cap
    if still_needed > 0:
        for c in sorted(cats, key=lambda x: -category_sizes[x]):
            if still_needed <= 0:
                break
            if quotas[c] < category_sizes[c]:
                add = min(still_needed, category_sizes[c] - quotas[c])
                quotas[c] += add
                still_needed -= add

    return quotas


# ---------------------------------------------------------------------------
# Task selection within a category
# ---------------------------------------------------------------------------

def select_tasks(
    tasks: list[dict],
    n: int,
    ablation_ids: set[str],
) -> list[dict]:
    """
    Select up to `n` tasks from `tasks` using the priority:
      1. Has ablation data  (prefer)
      2. Difficulty: expert > hard > medium > easy
      3. task_id alphabetical (deterministic tie-break)
    """
    def sort_key(t: dict):
        has_abl = 0 if t["task_id"] in ablation_ids else 1
        diff = DIFFICULTY_ORDER.get(t["difficulty"], 99)
        return (has_abl, diff, t["task_id"])

    sorted_tasks = sorted(tasks, key=sort_key)
    return sorted_tasks[:n]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Load dataset
    with open(DATASET_PATH) as f:
        all_tasks: list[dict] = json.load(f)

    # Attach refined_category to each task (in-memory only)
    for t in all_tasks:
        t["refined_category"] = refined_category(t)

    # Load ablation task_ids
    ablation_ids = load_ablation_task_ids()

    # Group by refined_category
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for t in all_tasks:
        by_cat[t["refined_category"]].append(t)

    cat_sizes = {c: len(tasks) for c, tasks in by_cat.items()}

    # Compute quotas
    quotas = compute_quotas(cat_sizes, TARGET_N, CAP_PER_CATEGORY)

    # Select tasks
    selected: list[dict] = []
    cat_breakdown: dict[str, dict] = {}

    for cat in sorted(by_cat.keys()):
        q = quotas[cat]
        chosen = select_tasks(by_cat[cat], q, ablation_ids)
        selected.extend(chosen)
        with_abl = sum(1 for t in chosen if t["task_id"] in ablation_ids)
        diff_counts = dict(Counter(t["difficulty"] for t in chosen))
        cat_breakdown[cat] = {
            "quota": q,
            "selected": len(chosen),
            "pool_size": cat_sizes[cat],
            "with_ablation": with_abl,
            "difficulty": diff_counts,
        }

    # Summary table
    print(f"\n{'Category':<35} {'Pool':>6} {'Quota':>6} {'Selected':>9} {'W/Abl':>6}  Difficulty")
    print("-" * 90)
    for cat in sorted(cat_breakdown.keys()):
        b = cat_breakdown[cat]
        diff_str = "  ".join(
            f"{d}:{b['difficulty'].get(d,0)}"
            for d in ("expert", "hard", "medium", "easy")
            if b['difficulty'].get(d, 0) > 0
        )
        print(
            f"{cat:<35} {b['pool_size']:>6} {b['quota']:>6} {b['selected']:>9} "
            f"{b['with_ablation']:>6}  {diff_str}"
        )
    print("-" * 90)
    total_abl = sum(b["with_ablation"] for b in cat_breakdown.values())
    print(f"{'TOTAL':<35} {sum(cat_sizes.values()):>6} {sum(quotas.values()):>6} "
          f"{len(selected):>9} {total_abl:>6}")

    # Difficulty distribution
    overall_diff = Counter(t["difficulty"] for t in selected)
    print(f"\nDifficulty distribution ({len(selected)} tasks):")
    for d in ("expert", "hard", "medium", "easy"):
        n = overall_diff.get(d, 0)
        bar = "#" * n
        print(f"  {d:<8} {n:>3}  {bar}")

    # Category coverage
    n_cats = len(cat_breakdown)
    print(f"\nCategory coverage: {n_cats} categories")
    print(f"Tasks with ablation data: {total_abl}/{len(selected)} ({100*total_abl/len(selected):.1f}%)")

    # Build output
    output_tasks = [
        {
            "task_id": t["task_id"],
            "category": t["category"],
            "refined_category": t["refined_category"],
            "difficulty": t["difficulty"],
        }
        for t in selected
    ]

    output = {
        "version": "2.0",
        "n_tasks": len(selected),
        "selection_date": SELECTION_DATE,
        "categories": cat_breakdown,
        "tasks": output_tasks,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWrote {len(selected)} tasks to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
