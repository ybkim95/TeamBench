#!/usr/bin/env python3
"""Run heterogeneous team experiments.

Tests different model combinations for Planner/Executor/Verifier roles
on the 28-task cross-model subset.

Usage:
    python scripts/run_hetero_ablation.py --config all --output shared/ablation_results/hetero_seed0.json
    python scripts/run_hetero_ablation.py --config plan_up --output shared/ablation_results/hetero_plan_up.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

# Allow running from repo root without installing the package.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.ablation import AblationCondition, run_ablation_condition
from harness.adapters import create_adapter
from harness.run_all import discover_tasks, setup_run, grade_run


TASKS = [  # Same 28-task cross-model subset
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

CONFIGS: dict[str, dict[str, str]] = {
    # Upgrade only the Planner to a stronger model
    "plan_up": {
        "planner": "gpt-5-mini",
        "executor": "gemini-3.1-flash-lite-preview",
        "verifier": "gemini-3.1-flash-lite-preview",
    },
    # Upgrade only the Executor to a stronger model
    "exec_up": {
        "planner": "gemini-3.1-flash-lite-preview",
        "executor": "gpt-5-mini",
        "verifier": "gemini-3.1-flash-lite-preview",
    },
    # Upgrade only the Verifier to a stronger model
    "verify_up": {
        "planner": "gemini-3.1-flash-lite-preview",
        "executor": "gemini-3.1-flash-lite-preview",
        "verifier": "gpt-5-mini",
    },
    # Cross-family mix: OpenAI planner, Gemini executor, OpenAI verifier
    "cross_family": {
        "planner": "gpt-5-mini",
        "executor": "gemini-3-flash-preview",
        "verifier": "gpt-5-nano",
    },
    # Premium planner (Claude) with mid-tier executor and light verifier
    "premium_plan": {
        "planner": "claude-sonnet-4-6-20250514",
        "executor": "gemini-3-flash-preview",
        "verifier": "gpt-5-nano",
    },
    # === Same-family controlled configs (Gemini only) ===
    # Isolate role quality from cross-family communication effects
    "plan_up_gemini": {
        "planner": "gemini-3-flash-preview",
        "executor": "gemini-3.1-flash-lite-preview",
        "verifier": "gemini-3.1-flash-lite-preview",
    },
    "exec_up_gemini": {
        "planner": "gemini-3.1-flash-lite-preview",
        "executor": "gemini-3-flash-preview",
        "verifier": "gemini-3.1-flash-lite-preview",
    },
    "verify_up_gemini": {
        "planner": "gemini-3.1-flash-lite-preview",
        "executor": "gemini-3.1-flash-lite-preview",
        "verifier": "gemini-3-flash-preview",
    },
}


def run_hetero_config(
    config_name: str,
    model_config: dict[str, str],
    tasks: list[str],
    tasks_dir: str,
    seed: int,
    runs_base: str,
) -> list[dict]:
    """Run a single heterogeneous config across all tasks for a given seed."""
    # Build a fallback adapter using the executor model (arbitrary choice for
    # conditions that don't use per-role adapters; HETERO always uses model_config).
    fallback_model = model_config.get("executor", next(iter(model_config.values())))
    adapter = create_adapter(model=fallback_model, temperature=0.2)

    run_records: list[dict] = []
    total = len(tasks)

    for i, task_name in enumerate(tasks, 1):
        print(f"  [{i}/{total}] {config_name} x {task_name} (seed={seed})", flush=True)
        start_time = time.time()
        record: dict = {
            "config": config_name,
            "model_config": model_config,
            "task_id": task_name,
            "seed": seed,
            "run_id": "",
            "run_dir": "",
            "pass": False,
            "partial_score": 0.0,
            "elapsed_sec": 0.0,
            "failure_modes": [],
            "error": None,
        }

        try:
            run_id, run_dir, task_dir = setup_run(task_name, tasks_dir, runs_base, seed=seed)
            record["run_id"] = run_id
            record["run_dir"] = run_dir

            # Store metadata
            meta_path = os.path.join(run_dir, "run_meta.json")
            if os.path.isfile(meta_path):
                with open(meta_path, "r") as mf:
                    meta = json.load(mf)
                meta["condition"] = "hetero"
                meta["model_config"] = model_config
                meta["hetero_config_name"] = config_name
                with open(meta_path, "w") as mf:
                    json.dump(meta, mf, indent=2)

            orch_result = run_ablation_condition(
                condition=AblationCondition.HETERO,
                task_dir=task_dir,
                run_dir=run_dir,
                adapter=adapter,
                max_turns=20,
                max_remediation=2,
                model_config=model_config,
            )

            elapsed = time.time() - start_time
            score = grade_run(task_name, task_dir, run_dir)
            passed = bool(score.get("pass", False))
            partial = score.get("secondary", {}).get(
                "partial_score", 1.0 if passed else 0.0
            )
            record.update({
                "pass": passed,
                "partial_score": float(partial),
                "elapsed_sec": round(elapsed, 1),
                "failure_modes": score.get("failure_modes", []),
            })
            status = "PASS" if passed else "FAIL"
            print(
                f"    {status} (partial={partial:.2f}, {elapsed:.1f}s, "
                f"{orch_result.total_turns} turns)",
                flush=True,
            )

        except Exception as e:
            record["error"] = str(e)
            record["elapsed_sec"] = round(time.time() - start_time, 1)
            print(f"    ERROR: {e}", flush=True)

        run_records.append(record)

    return run_records


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Run heterogeneous team ablation experiments."
    )
    ap.add_argument(
        "--config",
        default="all",
        help=(
            "Config name to run, or 'all' to run all configs. "
            f"Available: {', '.join(CONFIGS)} (default: all)"
        ),
    )
    ap.add_argument(
        "--output",
        default="shared/ablation_results/hetero_seed0.json",
        help="Output JSON path (default: shared/ablation_results/hetero_seed0.json)",
    )
    ap.add_argument(
        "--tasks-dir",
        default="tasks",
        help="Tasks directory (default: tasks)",
    )
    ap.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Seed to use (default: 0)",
    )
    ap.add_argument(
        "--tasks",
        nargs="*",
        default=None,
        help="Subset of tasks to run (default: all 28 cross-model tasks)",
    )
    args = ap.parse_args()

    # Load .env if present
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.isfile(env_path):
        with open(env_path) as ef:
            for line in ef:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())

    # Resolve config(s) to run
    if args.config == "all":
        configs_to_run = list(CONFIGS.items())
    elif args.config in CONFIGS:
        configs_to_run = [(args.config, CONFIGS[args.config])]
    else:
        ap.error(f"Unknown config '{args.config}'. Choose from: {', '.join(CONFIGS)} or 'all'")

    tasks_dir = os.path.abspath(args.tasks_dir)
    task_names = args.tasks if args.tasks else TASKS

    # Filter to tasks that actually exist on disk
    available = set(discover_tasks(tasks_dir))
    missing = [t for t in task_names if t not in available]
    if missing:
        print(f"WARNING: {len(missing)} tasks not found on disk and will be skipped: {missing}")
    task_names = [t for t in task_names if t in available]

    if not task_names:
        print("ERROR: No valid tasks to run.", file=sys.stderr)
        sys.exit(1)

    runs_base = os.path.join(os.path.dirname(os.path.abspath(args.output)), "hetero_runs")

    print("TeamBench Heterogeneous Team Ablation")
    print(f"Configs: {[c for c, _ in configs_to_run]}")
    print(f"Tasks:   {len(task_names)}")
    print(f"Seed:    {args.seed}")
    print("=" * 60)

    all_runs: list[dict] = []

    for config_name, model_config in configs_to_run:
        print(f"\n--- Config: {config_name} ---")
        for role, mdl in model_config.items():
            print(f"  {role}: {mdl}")

        records = run_hetero_config(
            config_name=config_name,
            model_config=model_config,
            tasks=task_names,
            tasks_dir=tasks_dir,
            seed=args.seed,
            runs_base=runs_base,
        )
        all_runs.extend(records)

    # Compute per-config summary
    per_config: dict[str, dict] = {}
    for cfg_name, _ in configs_to_run:
        cfg_runs = [r for r in all_runs if r["config"] == cfg_name]
        passes = sum(1 for r in cfg_runs if r["pass"])
        total = len(cfg_runs)
        avg_partial = sum(r["partial_score"] for r in cfg_runs) / max(1, total)
        per_config[cfg_name] = {
            "passes": passes,
            "total": total,
            "success_rate": round(passes / max(1, total), 4),
            "avg_partial": round(avg_partial, 4),
            "model_config": CONFIGS[cfg_name],
        }

    report = {
        "experiment": "hetero_ablation",
        "seed": args.seed,
        "tasks": task_names,
        "configs": {name: cfg for name, cfg in CONFIGS.items() if name in dict(configs_to_run)},
        "completed": datetime.now(timezone.utc).isoformat(),
        "per_config": per_config,
        "runs": all_runs,
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n{'=' * 60}")
    print("HETERO ABLATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"  {'Config':<20} {'Passes':>6}  {'Total':>5}  {'Rate':>6}  {'AvgPartial':>10}")
    for cfg_name, summary in per_config.items():
        print(
            f"  {cfg_name:<20} {summary['passes']:>6}  {summary['total']:>5}  "
            f"{summary['success_rate']:>6.1%}  {summary['avg_partial']:>10.4f}"
        )
    print(f"\n  Report: {args.output}")


if __name__ == "__main__":
    main()
