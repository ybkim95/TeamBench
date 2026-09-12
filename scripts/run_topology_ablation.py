#!/usr/bin/env python3
"""Run topology ablation experiments.

Compares 4 coordination topologies against the standard conditions
on a subset of tasks.

Usage:
    python scripts/run_topology_ablation.py --model gemini-3-flash-preview
    python scripts/run_topology_ablation.py --model vllm:Qwen/Qwen3-32B@http://localhost:8006/v1
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.ablation import run_full_ablation, AblationCondition

# 14-task subset covering diverse categories for topology comparison
# Chosen to include tasks where team helps AND hurts (to measure topology sensitivity)
TASKS = [
    "MULTI1_fullstack_fix",   # Multi-layer: team helps strongly
    "TEST1_spec_to_tests",    # Testing: high TNI
    "O2_incident_rootcause",  # Ops/incident: investigation benefits from iteration
    "PIPE1_etl_fix",          # Pipeline: high TNI
    "TRAP1_spec_conflict",    # Adversarial: spec traps, verify-first should help
    "TRAP3_metric_mirage",    # Adversarial: measurement bugs
    "CROSS1_api_contract",    # Cross-codebase: iterative planning should help
    "CRYPTO1_nonce_reuse",    # Security: dual exec diversity may help
    "DIST1_queue_race",       # Distributed: complex interactions
    "SEC1_vuln_patch",        # Security: multiple valid approaches
    "D1_schema_drift",        # Data: workspace analysis valuable
    "INC1_cascade_failure",   # Incident: investigation-heavy
    "SPEC1_feature_impl",     # Spec-driven: planning important
    "NEG1_tradeoff_config",   # Negotiation: subtle requirements
]

# Topology conditions + baselines for comparison
TOPOLOGY_CONDITIONS = [
    AblationCondition.ORACLE,          # Single agent upper bound
    AblationCondition.FULL,            # Standard 3-phase pipeline
    AblationCondition.TOPO_ITERATIVE,  # Multi-round planner<->executor
    AblationCondition.TOPO_DUAL_EXEC,  # Parallel executors + selection
    AblationCondition.TOPO_VERIFY_FIRST,  # Gap analysis -> fix -> verify
    AblationCondition.TOPO_SELF_CHECK,    # Structured single-agent
]


def main():
    ap = argparse.ArgumentParser(description="Run topology ablation experiments")
    ap.add_argument("--model", required=True, help="Model adapter string")
    ap.add_argument("--seeds", nargs="+", type=int, default=[0],
                    help="Seeds to evaluate (default: [0])")
    ap.add_argument("--output", default="shared/ablation_results/topology_ablation.json",
                    help="Output path")
    ap.add_argument("--tasks-dir", default="tasks", help="Tasks directory")
    args = ap.parse_args()

    print(f"Topology Ablation Experiment")
    print(f"  Model: {args.model}")
    print(f"  Tasks: {len(TASKS)}")
    print(f"  Conditions: {len(TOPOLOGY_CONDITIONS)}")
    print(f"  Seeds: {args.seeds}")
    print(f"  Total runs: {len(TASKS) * len(TOPOLOGY_CONDITIONS) * len(args.seeds)}")
    print(f"  Output: {args.output}")
    print()

    run_full_ablation(
        model=args.model,
        tasks=TASKS,
        seeds=args.seeds,
        tasks_dir=args.tasks_dir,
        output=args.output,
        conditions=TOPOLOGY_CONDITIONS,
    )
    print(f"\nDone! Results saved to {args.output}")


if __name__ == "__main__":
    main()
