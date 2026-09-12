#!/usr/bin/env python3
"""Middle-start worker for the 100-task leaderboard ablation.

Pairs with run_leaderboard_100_ablation.py (forward) and run_lb100_reverse.py
(reverse). Two instances of this script — one with --mid-direction forward,
one with --mid-direction backward — give 4 workers approaching the work
from 4 starting points, sharing one --output checkpoint via O_APPEND.

mid-direction=forward:  task order = TASKS[mid:] + TASKS[:mid]
                         (start at middle, wrap forward to start)
mid-direction=backward: task order = reversed(TASKS[:mid]) + reversed(TASKS[mid:])
                         (start just before middle, walk back to start, wrap to end)

Conditions iterate in forward order in both cases (the existing FWD/REV
already cover both condition orderings).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.ablation import run_full_ablation, AblationCondition

TASKS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "leaderboard", "data", "leaderboard_100_tasks.json",
)
with open(TASKS_FILE) as f:
    _data = json.load(f)
    _seen = set()
    TASKS = []
    for t in _data["tasks"]:
        if t["task_id"] not in _seen:
            _seen.add(t["task_id"])
            TASKS.append(t["task_id"])

CONDITIONS_FORWARD = [
    AblationCondition.ORACLE,
    AblationCondition.RESTRICTED,
    AblationCondition.TEAM_NO_VERIFY,
    AblationCondition.TEAM_NO_PLAN,
    AblationCondition.FULL,
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--seeds", nargs="+", type=int, default=[0])
    ap.add_argument("--output", required=True,
                    help="Same --output as the other workers so they share the checkpoint")
    ap.add_argument("--tasks-dir", default="tasks")
    ap.add_argument("--mid-direction", choices=["forward", "backward"], required=True)
    ap.add_argument("--start-frac", type=float, default=0.5,
                    help="Fraction of task list to start from (default 0.5 = middle)")
    args = ap.parse_args()

    mid = max(1, min(len(TASKS) - 1, int(len(TASKS) * args.start_frac)))

    if args.mid_direction == "forward":
        tasks_ordered = TASKS[mid:] + TASKS[:mid]
    else:  # backward
        tasks_ordered = list(reversed(TASKS[:mid])) + list(reversed(TASKS[mid:]))

    print(f"TeamBench 100-Task Leaderboard Ablation (MIDDLE WORKER, {args.mid_direction})")
    print("=" * 60)
    print(f"  Model:          {args.model}")
    print(f"  Tasks:          {len(tasks_ordered)} (start_frac={args.start_frac}, mid_idx={mid})")
    print(f"  Seeds:          {args.seeds}")
    print(f"  Conditions:     {[c.value for c in CONDITIONS_FORWARD]} (forward)")
    print(f"  Mid direction:  {args.mid_direction}")
    print(f"  First 5 tasks:  {tasks_ordered[:5]}")
    print(f"  Output:         {args.output} (shared with FWD/REV workers)")
    print("=" * 60)

    run_full_ablation(
        model=args.model,
        tasks=tasks_ordered,
        seeds=args.seeds,
        tasks_dir=args.tasks_dir,
        output=args.output,
        conditions=CONDITIONS_FORWARD,
    )


if __name__ == "__main__":
    main()
