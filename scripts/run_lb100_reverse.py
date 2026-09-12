#!/usr/bin/env python3
"""Reverse-iteration worker for the 100-task leaderboard ablation.

Mirror of run_leaderboard_100_ablation.py but iterates conditions and tasks
in reversed order. Run alongside the forward worker against the same --output
to halve wall time. Checkpoint append is atomic; collisions near the meet
point cost at most a few duplicated runs (dedup happens at resume time).
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
                    help="Same --output as the forward worker so they share the checkpoint")
    ap.add_argument("--tasks-dir", default="tasks")
    args = ap.parse_args()

    tasks_reversed = list(reversed(TASKS))
    conditions_reversed = list(reversed(CONDITIONS_FORWARD))

    print(f"TeamBench 100-Task Leaderboard Ablation (REVERSE WORKER)")
    print(f"=" * 60)
    print(f"  Model:      {args.model}")
    print(f"  Tasks:      {len(tasks_reversed)} (reversed)")
    print(f"  Seeds:      {args.seeds}")
    print(f"  Conditions: {[c.value for c in conditions_reversed]}")
    print(f"  Output:     {args.output} (shared with forward worker)")
    print(f"=" * 60)

    run_full_ablation(
        model=args.model,
        tasks=tasks_reversed,
        seeds=args.seeds,
        tasks_dir=args.tasks_dir,
        output=args.output,
        conditions=conditions_reversed,
    )


if __name__ == "__main__":
    main()
