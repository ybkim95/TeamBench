#!/usr/bin/env python3
"""Full 147-task ablation with GPT-5-Mini.

This replicates the reference evaluation (Gemini 3 Flash) on a second model
to address the limitation that the full ablation was only run on one model.

Usage:
    python scripts/run_gpt5mini_full_ablation.py
    python scripts/run_gpt5mini_full_ablation.py --batch 1   # tasks 0-49
    python scripts/run_gpt5mini_full_ablation.py --batch 2   # tasks 50-99
    python scripts/run_gpt5mini_full_ablation.py --batch 3   # tasks 100+
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.ablation import run_full_ablation, AblationCondition
from harness.run_all import discover_tasks

MODEL = "gpt-5-mini"
CONDITIONS = [
    AblationCondition.ORACLE,
    AblationCondition.RESTRICTED,
    AblationCondition.TEAM_NO_VERIFY,
    AblationCondition.TEAM_NO_PLAN,
    AblationCondition.FULL,
]

# Exclude EA tasks (require special orchestrator) and tasks known to have issues
EXCLUDE_PREFIXES = ["EA"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=0,
                    help="Batch number (1=0-49, 2=50-99, 3=100+). 0=all")
    ap.add_argument("--seeds", nargs="+", type=int, default=[0])
    args = ap.parse_args()

    # Discover all tasks
    all_tasks = discover_tasks("tasks")
    tasks = [t for t in all_tasks
             if not any(t.startswith(p) for p in EXCLUDE_PREFIXES)]

    print(f"Total tasks: {len(tasks)} (excluded {len(all_tasks) - len(tasks)} EA tasks)")

    # Batch splitting
    if args.batch == 1:
        tasks = tasks[:50]
    elif args.batch == 2:
        tasks = tasks[50:100]
    elif args.batch == 3:
        tasks = tasks[100:]

    print(f"Running batch {'all' if args.batch == 0 else args.batch}: {len(tasks)} tasks")
    print(f"Model: {MODEL}")
    print(f"Conditions: {[c.value for c in CONDITIONS]}")
    print(f"Seeds: {args.seeds}")

    batch_suffix = f"_batch{args.batch}" if args.batch > 0 else ""
    outpath = os.path.join(
        "shared", "ablation_results",
        f"full_ablation_gpt5mini_seed{'_'.join(map(str, args.seeds))}{batch_suffix}.json"
    )

    run_full_ablation(
        model=MODEL,
        tasks=tasks,
        seeds=args.seeds,
        tasks_dir="tasks",
        output=outpath,
        conditions=CONDITIONS,
    )

    print(f"\nResults saved to {outpath}")


if __name__ == "__main__":
    main()
