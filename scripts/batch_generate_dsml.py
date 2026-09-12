#!/usr/bin/env python3
"""
Batch generator + validator for ALL DS (1-50) and ML (1-50) tasks.

Steps for EACH generator × seed:
  1. Import the generator, call generate(seed)
  2. Write workspace, spec.md, brief.md, expected.json to disk
  3. Run the check/validation script inside the workspace (if one exists)
  4. Verify cross-seed contamination resistance (seed A ≠ seed B)
  5. Log pass/fail for every task

Usage:
  python scripts/batch_generate_dsml.py  [--seeds 0,1,2]  [--workers 4]

Output:
  tasks/DS{i}_*/  and  tasks/ML{i}_*/    (on-disk task instances)
  logs/dsml_generation_report.json        (summary)
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# ──── Configuration ───────────────────────────────────────────────────────────

DS_RANGE = range(1, 51)
ML_RANGE = range(1, 51)

LOG_DIR  = os.path.join(ROOT, "logs")
TASK_DIR = os.path.join(ROOT, "tasks")
os.makedirs(LOG_DIR, exist_ok=True)

# Map generator module names → their file name stems
# e.g., gen_ds1_feature_leakage.py → generators.gen_ds1_feature_leakage
DS_NAMES = {
    1: "feature_leakage", 2: "missing_data_bias", 3: "class_imbalance",
    4: "timeseries_split", 5: "outlier_vs_signal", 6: "simpson_paradox",
    7: "data_pipeline_repair", 8: "ab_test_analysis", 9: "data_drift_detection",
    10: "fairness_audit", 11: "survival_censoring", 12: "bayesian_prior",
    13: "clustered_power", 14: "multicollinearity_suppressor",
    15: "heteroscedastic_inference", 16: "iv_validity",
    17: "panel_autocorrelation", 18: "simpsons_causal",
    19: "dependent_multiple_testing", 20: "rd_bandwidth",
    21: "cdc_out_of_order", 22: "scd_type2", 23: "fuzzy_dedup",
    24: "etl_idempotency", 25: "lineage_cycle",
    26: "schema_evolution_compat", 27: "deferred_fk",
    28: "timezone_reconcile", 29: "late_arriving_agg", 30: "data_contract",
    31: "target_encoding_leak", 32: "cyclical_encoding",
    33: "interaction_selection", 34: "polynomial_degree",
    35: "text_feature_trap", 36: "cardinality_encoding",
    37: "feature_importance", 38: "geospatial_projection",
    39: "lag_feature_lookahead", 40: "business_calendar",
    41: "cohort_retention", 42: "clv_discount_rate",
    43: "churn_censoring", 44: "attribution_position",
    45: "structural_break", 46: "multi_seasonal",
    47: "funnel_selection_bias", 48: "price_elasticity",
    49: "novelty_effect", 50: "substitution_demand",
}

ML_NAMES = {
    1: "gradient_bug", 2: "overfitting_diagnosis", 3: "tokenizer_mismatch",
    4: "metric_selection", 5: "data_augmentation_leak",
    6: "embedding_dim_mismatch", 7: "hyperparameter_search",
    8: "distributed_training", 9: "model_serving_bug",
    10: "evaluation_contamination", 11: "lr_warmup_decay",
    12: "residual_init", 13: "amp_clip_order",
    14: "label_smooth_pad", 15: "kd_temperature",
    16: "contrastive_false_neg", 17: "ema_bn_stats",
    18: "curriculum_invert", 19: "causal_mask_offbyone",
    20: "sinusoidal_pe_freq", 21: "mha_split_dim",
    22: "norm_placement", 23: "cross_attn_swap",
    24: "cls_pooling", 25: "padding_mask",
    26: "rope_asymmetric", 27: "normalization_leak",
    28: "multilabel_stratify", 29: "tokenizer_truncation",
    30: "augment_after_norm", 31: "class_weight_invert",
    32: "worker_rng_fork", 33: "feature_store_pit",
    34: "dataset_version", 35: "calibration_double_temp",
    36: "threshold_on_test", 37: "ab_novelty_effect",
    38: "metric_aggregation", 39: "quantization_bn_mode",
    40: "shadow_eval_mismatch", 41: "drift_prediction_shift",
    42: "pruning_magnitude", 43: "reward_shaping",
    44: "gan_minimax_loss", 45: "ssl_no_predictor",
    46: "fewshot_overlap", 47: "multitask_weight",
    48: "replay_fifo_bias", 49: "fedavg_noisy_client",
    50: "active_uncalibrated",
}


# ──── Result structure ────────────────────────────────────────────────────────

@dataclass
class TaskResult:
    task_id: str
    seed: int
    generated: bool = False
    written: bool = False
    check_passed: bool | None = None
    cross_seed_ok: bool | None = None
    spec_chars: int = 0
    brief_chars: int = 0
    workspace_files: int = 0
    expected_keys: int = 0
    error: str = ""
    duration_sec: float = 0.0


# ──── Core logic ─────────────────────────────────────────────────────────────

def _import_generator(category: str, idx: int, name: str):
    """Import and return the Generator class from the generator module."""
    module_name = f"generators.gen_{category}{idx}_{name}"
    mod = importlib.import_module(module_name)
    return mod.Generator()


def _run_check_script(workspace_dir: str, gen_task) -> bool | None:
    """Run any check_*.py script inside the workspace directory."""
    check_files = [
        f for f in (gen_task.workspace_files or {})
        if f.startswith("check_") and f.endswith(".py")
    ]
    if not check_files:
        return None  # No check script

    for check_file in check_files:
        check_path = os.path.join(workspace_dir, check_file)
        if not os.path.exists(check_path):
            continue
        try:
            result = subprocess.run(
                [sys.executable, check_path],
                cwd=workspace_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                return False
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False
    return True


def process_task(category: str, idx: int, name: str, seed: int) -> TaskResult:
    """Generate a single task instance, write to disk, and validate."""
    task_id = f"{'DS' if category == 'ds' else 'ML'}{idx}_{name}"
    result = TaskResult(task_id=task_id, seed=seed)
    t0 = time.time()

    try:
        # 1. Import and generate
        gen = _import_generator(category, idx, name)
        gt = gen.generate(seed)
        result.generated = True
        result.spec_chars = len(gt.spec_md)
        result.brief_chars = len(gt.brief_md)
        result.workspace_files = len(gt.workspace_files)
        result.expected_keys = len(gt.expected)

        # 2. Write to disk
        seed_suffix = f"_seed{seed}"
        task_dir = os.path.join(TASK_DIR, f"{task_id}{seed_suffix}")
        workspace_dir = os.path.join(task_dir, "workspace")
        reports_dir = os.path.join(task_dir, "reports")

        gen.write_to_disk(gt, workspace_dir, reports_dir, task_dir)
        result.written = True

        # 3. Run check script (only for seed 0 to save time)
        if seed == 0:
            result.check_passed = _run_check_script(workspace_dir, gt)

        # 4. Cross-seed validation (only for seeds 0 vs 1)
        if seed == 0:
            try:
                gt_other = gen.generate(1)
                result.cross_seed_ok = (
                    gt.expected != gt_other.expected and
                    gt.workspace_files != gt_other.workspace_files
                )
            except Exception:
                result.cross_seed_ok = False

    except Exception as e:
        result.error = f"{type(e).__name__}: {str(e)[:200]}"
        traceback.print_exc()

    result.duration_sec = round(time.time() - t0, 2)
    return result


def main():
    parser = argparse.ArgumentParser(description="Batch generate and validate DS/ML tasks")
    parser.add_argument("--seeds", default="0,1,2", help="Comma-separated seeds")
    parser.add_argument("--workers", type=int, default=4, help="Parallel workers")
    parser.add_argument("--category", default="all", choices=["ds", "ml", "all"])
    args = parser.parse_args()
    seeds = [int(s) for s in args.seeds.split(",")]

    # Build task list
    tasks = []
    if args.category in ("ds", "all"):
        for idx, name in DS_NAMES.items():
            for seed in seeds:
                tasks.append(("ds", idx, name, seed))
    if args.category in ("ml", "all"):
        for idx, name in ML_NAMES.items():
            for seed in seeds:
                tasks.append(("ml", idx, name, seed))

    total = len(tasks)
    print(f"\n{'='*70}")
    print(f"  TeamBench DS/ML Batch Generator + Validator")
    print(f"  Tasks: {total} ({len(seeds)} seeds × {total // len(seeds)} generators)")
    print(f"  Workers: {args.workers}")
    print(f"  Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*70}\n")

    results: list[TaskResult] = []
    completed = 0

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(process_task, cat, idx, name, seed): (cat, idx, name, seed)
            for cat, idx, name, seed in tasks
        }

        for future in as_completed(futures):
            cat, idx, name, seed = futures[future]
            try:
                r = future.result()
            except Exception as e:
                r = TaskResult(
                    task_id=f"{'DS' if cat == 'ds' else 'ML'}{idx}_{name}",
                    seed=seed,
                    error=f"ProcessError: {str(e)[:200]}"
                )
            results.append(r)
            completed += 1

            status = "✓" if r.generated and not r.error else "✗"
            check_str = ""
            if r.check_passed is True:
                check_str = " [check:PASS]"
            elif r.check_passed is False:
                check_str = " [check:FAIL]"
            cross_str = ""
            if r.cross_seed_ok is True:
                cross_str = " [cross-seed:OK]"
            elif r.cross_seed_ok is False:
                cross_str = " [cross-seed:FAIL]"

            print(f"  [{completed:3d}/{total}] {status} {r.task_id} seed={r.seed} "
                  f"({r.duration_sec:.1f}s) "
                  f"spec={r.spec_chars}c brief={r.brief_chars}c "
                  f"files={r.workspace_files}{check_str}{cross_str}"
                  f"{' ERR: ' + r.error[:60] if r.error else ''}")

    # ── Summary ────────────────────────────────────────────────────────
    n_generated = sum(1 for r in results if r.generated)
    n_written = sum(1 for r in results if r.written)
    n_errors = sum(1 for r in results if r.error)
    n_check_pass = sum(1 for r in results if r.check_passed is True)
    n_check_fail = sum(1 for r in results if r.check_passed is False)
    n_cross_ok = sum(1 for r in results if r.cross_seed_ok is True)
    n_cross_fail = sum(1 for r in results if r.cross_seed_ok is False)

    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"  Generated: {n_generated}/{total}")
    print(f"  Written:   {n_written}/{total}")
    print(f"  Errors:    {n_errors}/{total}")
    print(f"  Check scripts: {n_check_pass} pass, {n_check_fail} fail")
    print(f"  Cross-seed:    {n_cross_ok} OK, {n_cross_fail} fail")
    print(f"{'='*70}")

    # Save report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_tasks": total,
        "generated": n_generated,
        "written": n_written,
        "errors": n_errors,
        "check_pass": n_check_pass,
        "check_fail": n_check_fail,
        "cross_seed_ok": n_cross_ok,
        "cross_seed_fail": n_cross_fail,
        "failed_tasks": [
            asdict(r) for r in results if r.error
        ],
        "check_failures": [
            asdict(r) for r in results if r.check_passed is False
        ],
        "cross_seed_failures": [
            asdict(r) for r in results if r.cross_seed_ok is False
        ],
        "all_results": [asdict(r) for r in results],
    }
    report_path = os.path.join(LOG_DIR, "dsml_generation_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report saved to: {report_path}")

    # Non-zero exit if any errors
    if n_errors > 0:
        print(f"\n  WARNING: {n_errors} tasks had errors. Review the report.")
        sys.exit(1)


if __name__ == "__main__":
    main()
