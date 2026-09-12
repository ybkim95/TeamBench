#!/usr/bin/env python3
"""Budget-matched Solo runner.

Closes the reviewer-2 attack that the team gain is just "more compute".
The Solo gets the team's full combined turn budget (Planner 15 + Executor 25
+ Verifier 10 = 50 turns) and runs with full spec access on the cross-provider
25-task subset.

Usage:
    python scripts/run_budget_matched_solo.py --model gemini-3-flash-preview
    python scripts/run_budget_matched_solo.py --model gemini-3-flash-preview --seeds 0
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

DEFAULT_TASKS_FILE = os.path.join(
    REPO, "shared/role_ablation/tasks_25.json"
)
DEFAULT_OUT_DIR = os.path.join(REPO, "shared/ablation_results")


def load_tasks_25(path: str):
    if not os.path.isfile(path):
        # Fall back to harness's stratified subset definition
        return [
            "MULTI1_polyglot_build", "TEST1_spec_to_tests", "O2_incident_rootcause",
            "PIPE1_etl_fix", "TRAP1_spec_conflict", "TRAP3_metric_mirage",
            "TRAP5_security_theater", "CROSS1_api_contract", "CROSS3_protocol_bridge",
            "CRYPTO1_nonce_reuse", "DIST1_queue_race", "SEC1_vuln_patch",
            "SEC3_crypto_upgrade", "D1_schema_drift", "D8_csv_cleanup",
            "TEST2_regression", "TEST5_mutation_resistant", "O1_service_health",
            "O3_log_analysis", "P1_policy_config", "P3_access_control",
            "SPEC1_feature_impl", "SPEC3_data_model", "INC1_cascade_failure",
            "IR1_evidence_qa",
        ][:25]
    d = json.load(open(path))
    if isinstance(d, list):
        return [t.get("task_id") if isinstance(t, dict) else t for t in d][:25]
    if isinstance(d, dict) and "tasks" in d:
        return [t.get("task_id") if isinstance(t, dict) else t for t in d["tasks"]][:25]
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True,
                    help="e.g. gemini-3-flash-preview, claude-haiku-4-5-20251001, gpt-5.4-mini")
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--tasks-file", default=DEFAULT_TASKS_FILE)
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    ap.add_argument("--limit", type=int, default=None,
                    help="Only run the first N tasks (for smoke tests)")
    args = ap.parse_args()

    from harness.ablation import AblationCondition, run_full_ablation

    tasks = load_tasks_25(args.tasks_file)
    if args.limit:
        tasks = tasks[: args.limit]

    model_tag = args.model.replace("/", "_").replace("-", "").replace(".", "")
    out_path = os.path.join(args.out_dir, f"budget_matched_solo_{model_tag}.json")
    print(f"[budget-solo] tasks={len(tasks)} seeds={args.seeds} model={args.model}")
    print(f"[budget-solo] out={out_path}")

    t0 = time.time()
    result = run_full_ablation(
        model=args.model,
        tasks=tasks,
        seeds=args.seeds,
        tasks_dir=os.path.join(REPO, "tasks"),
        output=out_path,
        max_turns=20,  # ignored for ORACLE_BUDGET_MATCHED (overridden to 50)
        conditions=[AblationCondition.ORACLE_BUDGET_MATCHED],
    )
    elapsed = time.time() - t0
    print(f"[budget-solo] done in {elapsed:.0f}s -> {out_path}")


if __name__ == "__main__":
    main()
