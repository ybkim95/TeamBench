#!/usr/bin/env python3
"""Run full 5-condition ablation on the 100-task leaderboard set.

This is the CORRECT way to evaluate models for the leaderboard.
The batch_runner.py only runs the Full Team condition — this script
runs all 5 conditions (Oracle, Restricted, No-Plan, No-Verify, Full)
needed to compute TNI, planning value, verification value, and uplift.

Usage:
    # Gemini (API model):
    python scripts/run_leaderboard_100_ablation.py --model gemini-3-flash-preview --seeds 0

    # vLLM-served model (start server first):
    python scripts/run_leaderboard_100_ablation.py \
        --model "vllm:Qwen/Qwen3-8B@http://localhost:8001/v1" --seeds 0

    # OpenAI API model:
    python scripts/run_leaderboard_100_ablation.py --model gpt-5-mini --seeds 0
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.ablation import run_full_ablation, AblationCondition

# Load 100-task set
TASKS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "leaderboard", "data", "leaderboard_100_tasks.json",
)

with open(TASKS_FILE) as f:
    _data = json.load(f)
    # Deduplicate
    _seen = set()
    TASKS = []
    for t in _data["tasks"]:
        if t["task_id"] not in _seen:
            _seen.add(t["task_id"])
            TASKS.append(t["task_id"])

CONDITIONS = [
    AblationCondition.ORACLE,
    AblationCondition.RESTRICTED,
    AblationCondition.TEAM_NO_VERIFY,
    AblationCondition.TEAM_NO_PLAN,
    AblationCondition.FULL,
]


def main():
    ap = argparse.ArgumentParser(description="Run 5-condition ablation on 100-task leaderboard set")
    ap.add_argument("--model", required=True,
                    help="Model name (e.g., gemini-3-flash-preview, gpt-5-mini, "
                         "vllm:Qwen/Qwen3-8B@http://localhost:8001/v1)")
    ap.add_argument("--seeds", nargs="+", type=int, default=[0])
    ap.add_argument("--output", default=None,
                    help="Output JSON path (default: shared/ablation_results/lb100_{model}_seed{s}.json)")
    ap.add_argument("--tasks-dir", default="tasks")
    ap.add_argument("--conditions", nargs="+", default=None,
                    choices=["oracle", "restricted", "team_no_verify", "team_no_plan", "full"],
                    help="Run only specific conditions (default: all 5)")
    args = ap.parse_args()

    # Determine output path
    model_short = args.model.split("/")[-1].split("@")[0].replace(":", "_").lower()
    seeds_str = "_".join(str(s) for s in args.seeds)
    outpath = args.output or os.path.join(
        "shared", "ablation_results", f"lb100_{model_short}_seed{seeds_str}.json"
    )

    # Filter conditions if specified
    conditions = CONDITIONS
    if args.conditions:
        conditions = [AblationCondition(c) for c in args.conditions]

    print(f"TeamBench 100-Task Leaderboard Ablation")
    print(f"=" * 60)
    print(f"  Model:      {args.model}")
    print(f"  Tasks:      {len(TASKS)}")
    print(f"  Seeds:      {args.seeds}")
    print(f"  Conditions: {[c.value for c in conditions]}")
    print(f"  Output:     {outpath}")
    print(f"  Runs:       {len(TASKS) * len(args.seeds) * len(conditions)}")
    print(f"=" * 60)

    run_full_ablation(
        model=args.model,
        tasks=TASKS,
        seeds=args.seeds,
        tasks_dir=args.tasks_dir,
        output=outpath,
        conditions=conditions,
    )

    print(f"\nResults saved to {outpath}")


if __name__ == "__main__":
    main()
