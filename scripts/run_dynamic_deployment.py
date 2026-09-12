#!/usr/bin/env python3
"""Dynamic team deployment: adaptive policy that decides when to use teams.

Implements the paper's recommendation:
  - Oracle < 30%: deploy full 3-phase team (+15% expected uplift)
  - Oracle 30-80%: deploy Planner + Executor only (skip verifier)
  - Oracle > 80%: use single agent directly

Evaluates this policy against always-oracle and always-team baselines
using precomputed oracle scores to route each task.

Usage:
    python scripts/run_dynamic_deployment.py
"""
import argparse
import json
import os
import sys
import time
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.ablation import AblationCondition, run_ablation_condition
from harness.adapters import create_adapter
from harness.run_all import setup_run, grade_run

MODEL = "gemini-3-flash-preview"

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

THRESHOLD_LOW = 0.30
THRESHOLD_HIGH = 0.80


def load_oracle_scores():
    """Load precomputed oracle scores from existing ablation results."""
    scores = {}
    for path in sorted(
        glob.glob("shared/ablation_results/batch*_seed0_g3flash.json") +
        glob.glob("shared/ablation_results/ablation_*.json") +
        ["shared/ablation_results/crypto_dist_g3flash.json",
         "shared/ablation_results/trap_cross_g3flash.json"]
    ):
        if not os.path.exists(path):
            continue
        with open(path) as f:
            d = json.load(f)
        for run in d.get("runs", []):
            cond = run.get("condition", run.get("config", ""))
            if cond == "oracle":
                scores[run["task_id"]] = run.get("partial_score", 0)
    return scores


def decide_condition(oracle_score: float) -> AblationCondition:
    if oracle_score < THRESHOLD_LOW:
        return AblationCondition.FULL
    elif oracle_score > THRESHOLD_HIGH:
        return AblationCondition.ORACLE
    else:
        return AblationCondition.TEAM_NO_VERIFY


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    outpath = os.path.join("shared", "ablation_results",
                           f"dynamic_deployment_seed{args.seed}.json")
    tasks_dir = os.path.abspath("tasks")
    runs_base = os.path.join(os.path.dirname(outpath), "dynamic_runs")

    oracle_scores = load_oracle_scores()
    print(f"Loaded oracle scores for {len(oracle_scores)} tasks")

    adapter = create_adapter(model=MODEL, temperature=0.2)

    results = {
        "experiment": "dynamic_deployment",
        "model": MODEL, "seed": args.seed,
        "thresholds": {"low": THRESHOLD_LOW, "high": THRESHOLD_HIGH},
        "tasks": TASKS, "runs": [], "decisions": {},
    }

    # Resume
    if os.path.exists(outpath):
        with open(outpath) as f:
            existing = json.load(f)
        results["runs"] = existing.get("runs", [])
        results["decisions"] = existing.get("decisions", {})
        done = {r["task_id"] for r in results["runs"]}
    else:
        done = set()

    for i, task_id in enumerate(TASKS):
        if task_id in done:
            continue

        oracle_score = oracle_scores.get(task_id, 0.0)
        condition = decide_condition(oracle_score)

        results["decisions"][task_id] = {
            "oracle_score": oracle_score,
            "selected_condition": condition.value,
        }

        print(f"\n[{i+1}/{len(TASKS)}] {task_id}: oracle={oracle_score:.2f} -> {condition.value}")
        start = time.time()

        try:
            run_id, run_dir, task_dir = setup_run(task_id, tasks_dir, runs_base, seed=args.seed)

            run_ablation_condition(
                condition=condition,
                task_dir=task_dir,
                run_dir=run_dir,
                adapter=adapter,
            )

            elapsed = time.time() - start
            score = grade_run(task_id, task_dir, run_dir)
            partial = score.get("secondary", {}).get("partial_score",
                        1.0 if score.get("pass") else 0.0)
            passed = bool(score.get("pass", False))

            print(f"  {'PASS' if passed else 'FAIL'} (partial={partial:.2f}, {elapsed:.1f}s)")

            results["runs"].append({
                "task_id": task_id, "seed": args.seed,
                "oracle_score": oracle_score,
                "selected_condition": condition.value,
                "pass": passed, "partial_score": partial,
                "elapsed_sec": round(elapsed, 1),
            })
        except Exception as e:
            print(f"  ERROR: {e}")
            results["runs"].append({
                "task_id": task_id, "seed": args.seed,
                "oracle_score": oracle_score,
                "selected_condition": condition.value,
                "pass": False, "partial_score": 0, "error": str(e),
            })

        with open(outpath, "w") as f:
            json.dump(results, f, indent=2)

    # Summary
    runs = results["runs"]
    avg = sum(r["partial_score"] for r in runs) / len(runs) if runs else 0
    pr = sum(r["pass"] for r in runs) / len(runs) * 100 if runs else 0

    by_cond = {}
    for r in runs:
        c = r["selected_condition"]
        by_cond.setdefault(c, []).append(r)

    oracle_avg = sum(oracle_scores.get(t, 0) for t in TASKS) / len(TASKS)

    print(f"\n{'='*60}")
    print(f"DYNAMIC DEPLOYMENT SUMMARY")
    print(f"{'='*60}")
    print(f"Overall: avg={avg:.3f}  pass={pr:.1f}%  n={len(runs)}")
    for c, c_runs in sorted(by_cond.items()):
        c_avg = sum(r["partial_score"] for r in c_runs) / len(c_runs)
        print(f"  {c:20s}: avg={c_avg:.3f}  n={len(c_runs)}")
    print(f"\nAlways-oracle baseline: avg={oracle_avg:.3f}")
    print(f"Dynamic policy:         avg={avg:.3f}  ({'+' if avg >= oracle_avg else ''}{avg - oracle_avg:.3f})")
    print(f"\nSaved to {outpath}")


if __name__ == "__main__":
    main()
