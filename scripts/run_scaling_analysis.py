#!/usr/bin/env python3
"""Scaling analysis: team benefit vs communication budget (agent turns).

Tests whether team benefit comes from role structure or just from having
more compute. Varies Planner and Executor turn limits.

Usage:
    python scripts/run_scaling_analysis.py
    python scripts/run_scaling_analysis.py --configs planner_5 planner_25 oracle_50
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.ablation import AblationCondition, run_ablation_condition
from harness.adapters import create_adapter
from harness.run_all import setup_run, grade_run

TASKS = [
    "MULTI1_fullstack_fix", "TEST1_spec_to_tests", "O2_incident_rootcause",
    "PIPE1_etl_fix", "TRAP1_spec_conflict", "TRAP3_metric_mirage",
    "TRAP5_security_theater", "CROSS1_api_contract", "CROSS3_protocol_bridge",
    "CRYPTO1_nonce_reuse", "DIST1_queue_race", "SEC1_vuln_patch",
    "SEC3_crypto_upgrade", "D1_schema_drift", "D8_csv_cleanup",
    "TEST2_regression", "TEST5_mutation_resistant", "O1_service_health",
    "O3_log_analysis", "P1_policy_config", "P3_access_control",
    "SPEC1_feature_impl", "SPEC3_data_model", "INC1_cascade_failure",
    "INC4_dns_miscfg", "IR1_evidence_qa", "NEG1_tradeoff_config",
    "CR5_test_coverage",
]

MODEL = "gemini-3-flash-preview"

# Turn budget configurations
# "condition" determines the ablation mode; extra keys set turn limits
CONFIGS = {
    "planner_5":  {"condition": "full", "max_turns": 5},
    "planner_10": {"condition": "full", "max_turns": 10},
    "planner_15": {"condition": "full", "max_turns": 15},
    "planner_25": {"condition": "full", "max_turns": 25},
    "exec_10":    {"condition": "full", "max_turns": 10},
    "exec_25":    {"condition": "full", "max_turns": 25},
    "exec_40":    {"condition": "full", "max_turns": 40},
    "oracle_25":  {"condition": "oracle", "max_turns": 25},
    "oracle_50":  {"condition": "oracle", "max_turns": 50},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", nargs="+", default=list(CONFIGS.keys()))
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    outpath = os.path.join("shared", "ablation_results",
                           f"scaling_analysis_seed{args.seed}.json")
    tasks_dir = os.path.abspath("tasks")
    runs_base = os.path.join(os.path.dirname(outpath), "scaling_runs")

    adapter = create_adapter(model=MODEL, temperature=0.2)

    results = {
        "experiment": "scaling_analysis",
        "model": MODEL, "seed": args.seed,
        "tasks": TASKS,
        "configs": {k: CONFIGS[k] for k in args.configs},
        "runs": [],
    }

    # Resume
    if os.path.exists(outpath):
        with open(outpath) as f:
            existing = json.load(f)
        results["runs"] = existing.get("runs", [])
        done = {(r["config"], r["task_id"]) for r in results["runs"]}
    else:
        done = set()

    total = len(args.configs) * len(TASKS)
    completed = len(done)

    for config_name in args.configs:
        cfg = CONFIGS[config_name]
        condition = AblationCondition(cfg["condition"])
        max_turns = cfg.get("max_turns", 20)

        for task_id in TASKS:
            if (config_name, task_id) in done:
                completed += 1
                continue

            completed += 1
            print(f"\n[{completed}/{total}] {config_name} x {task_id}")
            start = time.time()

            try:
                run_id, run_dir, task_dir = setup_run(
                    task_id, tasks_dir, runs_base, seed=args.seed
                )

                run_ablation_condition(
                    condition=condition,
                    task_dir=task_dir,
                    run_dir=run_dir,
                    adapter=adapter,
                    max_turns=max_turns,
                )

                elapsed = time.time() - start
                score = grade_run(task_id, task_dir, run_dir)
                partial = score.get("secondary", {}).get("partial_score",
                            1.0 if score.get("pass") else 0.0)
                passed = bool(score.get("pass", False))

                print(f"  {'PASS' if passed else 'FAIL'} (partial={partial:.2f}, {elapsed:.1f}s)")

                results["runs"].append({
                    "config": config_name, "task_id": task_id,
                    "seed": args.seed, "condition": cfg["condition"],
                    "max_turns": max_turns,
                    "pass": passed, "partial_score": partial,
                    "elapsed_sec": round(elapsed, 1),
                })
            except Exception as e:
                print(f"  ERROR: {e}")
                results["runs"].append({
                    "config": config_name, "task_id": task_id,
                    "seed": args.seed, "error": str(e),
                    "partial_score": 0, "pass": False,
                })

            with open(outpath, "w") as f:
                json.dump(results, f, indent=2)

    # Summary
    print(f"\n{'='*60}")
    print("SCALING ANALYSIS SUMMARY")
    print(f"{'='*60}")
    for config_name in args.configs:
        runs = [r for r in results["runs"] if r["config"] == config_name]
        if not runs:
            continue
        scores = [r["partial_score"] for r in runs]
        avg = sum(scores) / len(scores)
        pr = sum(r["pass"] for r in runs) / len(runs) * 100
        print(f"  {config_name:15s}: avg={avg:.3f}  pass={pr:.1f}%  n={len(runs)}")
    print(f"\nSaved to {outpath}")


if __name__ == "__main__":
    main()
