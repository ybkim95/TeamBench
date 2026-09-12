"""recompute_paper_evidence.py.

Recompute three paper claims that did not have a persisted JSON source:

  1. Solo-stratified quintile uplift (Section "Capability Sweet-Spot")
  2. Evaluator vs grader confusion matrix (Section "Limits of LLM verification")
  3. Full task pool composition (Section "Task Construction")

Plus refresh:

  4. TeamBench-Verified leaderboard table from current per-model JSONs

Outputs land in shared/paper/ for direct inclusion as paper assets.

This script reads existing artefacts only. It does not launch any new runs.
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SHARED = REPO / "shared"
PAPER = SHARED / "paper"
PAPER.mkdir(parents=True, exist_ok=True)


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, centre - half), min(1.0, centre + half))


# ---------- 1. Solo-stratified quintile uplift -------------------------------

def recompute_quintile_solo() -> dict:
    """Stratify the 155-task reference ablation by the per-task SOLO score and
    report mean team uplift (full - oracle) within each quintile.
    """
    summary = json.loads((PAPER / "ablation_summary.json").read_text())
    rows = []
    for entry in summary["per_task"]:
        task_id = entry.get("task_id")
        oracle = entry.get("oracle")
        full = entry.get("team")
        if oracle is None or full is None or task_id is None:
            continue
        rows.append({
            "task_id": task_id,
            "solo": float(oracle),  # Solo == Oracle condition in the harness
            "full": float(full),
            "uplift_pp": (float(full) - float(oracle)) * 100.0,
        })
    rows.sort(key=lambda r: r["solo"])
    n = len(rows)
    if n == 0:
        return {"error": "no per-task data"}
    # Five equal-size quintiles by Solo score
    bins = [
        rows[i * n // 5: (i + 1) * n // 5] for i in range(5)
    ]
    out_quintiles = []
    for i, b in enumerate(bins, start=1):
        uplifts = [r["uplift_pp"] for r in b]
        solos = [r["solo"] for r in b]
        m = statistics.mean(uplifts)
        # 95% normal-approx CI on the mean
        if len(uplifts) > 1:
            se = statistics.stdev(uplifts) / math.sqrt(len(uplifts))
            ci = (m - 1.96 * se, m + 1.96 * se)
        else:
            ci = (m, m)
        out_quintiles.append({
            "quintile": i,
            "n": len(b),
            "solo_min": round(min(solos), 4),
            "solo_max": round(max(solos), 4),
            "mean_uplift_pp": round(m, 2),
            "ci95_low_pp": round(ci[0], 2),
            "ci95_high_pp": round(ci[1], 2),
        })
    return {
        "method": "Equal-size quintile stratification by per-task Solo (oracle) score; "
                  "mean per-task uplift in percentage points = 100 × (full - oracle).",
        "n_tasks": n,
        "quintiles": out_quintiles,
    }


# ---------- 2. Evaluator vs grader confusion matrix --------------------------

def recompute_evaluator_confusion() -> dict:
    """For role_ablation full-team runs (which always have a verifier turn),
    pair the verifier attestation verdict against the deterministic grader's
    pass field. Compute the confusion matrix and false-accept / false-reject
    rates.
    """
    per_run_jsonl = SHARED / "role_ablation" / "results" / "per_run.jsonl"
    cm = {"tp": 0, "fp": 0, "tn": 0, "fn": 0, "missing": 0, "total": 0}
    examples = []
    with per_run_jsonl.open() as fh:
        for line in fh:
            try:
                run = json.loads(line)
            except Exception:
                continue
            cm["total"] += 1
            grader_pass = bool(run.get("pass"))
            run_dir = Path(run.get("run_dir", ""))
            att = run_dir / "submission" / "attestation.json"
            if not att.exists():
                cm["missing"] += 1
                continue
            try:
                attest = json.loads(att.read_text())
            except Exception:
                cm["missing"] += 1
                continue
            v = (attest.get("verdict") or "").lower()
            verifier_pass = v in ("pass", "passed", "ok")
            if verifier_pass and grader_pass:
                cm["tp"] += 1
            elif verifier_pass and not grader_pass:
                cm["fp"] += 1
                if len(examples) < 5:
                    examples.append({
                        "task": run.get("task_id"),
                        "config": run.get("config"),
                        "run_dir": str(run_dir),
                    })
            elif not verifier_pass and not grader_pass:
                cm["tn"] += 1
            else:
                cm["fn"] += 1
    n_evaluated = cm["total"] - cm["missing"]
    n_grader_fail = cm["fp"] + cm["tn"]
    n_grader_pass = cm["tp"] + cm["fn"]
    false_accept_rate = cm["fp"] / n_grader_fail if n_grader_fail else None
    false_reject_rate = cm["fn"] / n_grader_pass if n_grader_pass else None
    fa_lo, fa_hi = (
        _wilson(cm["fp"], n_grader_fail) if n_grader_fail else (None, None)
    )
    fr_lo, fr_hi = (
        _wilson(cm["fn"], n_grader_pass) if n_grader_pass else (None, None)
    )
    return {
        "source": str(per_run_jsonl.relative_to(REPO)),
        "n_runs_total": cm["total"],
        "n_runs_with_attestation": n_evaluated,
        "n_runs_missing_attestation": cm["missing"],
        "confusion_matrix": {
            "true_positive": cm["tp"],
            "false_positive_false_accept": cm["fp"],
            "true_negative": cm["tn"],
            "false_negative_false_reject": cm["fn"],
        },
        "false_accept_rate": false_accept_rate,
        "false_accept_ci95": [fa_lo, fa_hi],
        "false_reject_rate": false_reject_rate,
        "false_reject_ci95": [fr_lo, fr_hi],
        "n_grader_fail_pool": n_grader_fail,
        "n_grader_pass_pool": n_grader_pass,
        "examples_false_accept": examples,
    }


# ---------- 3. Full task pool composition ------------------------------------

def recompute_pool_composition() -> dict:
    """Compose the full task pool from teambench_dataset.json plus task dirs
    on disk so the totals reported in the paper are reproducible.
    """
    ds_path = SHARED / "teambench_dataset.json"
    ds = json.loads(ds_path.read_text())
    cat_counts: dict[str, int] = defaultdict(int)
    diff_counts: dict[str, int] = defaultdict(int)
    prefix_counts: dict[str, int] = defaultdict(int)
    for item in ds:
        cat_counts[item.get("category", "Unknown")] += 1
        diff_counts[item.get("difficulty", "unknown")] += 1
        tid = item.get("task_id", "")
        # split prefix at first _
        prefix = tid.split("_")[0] if "_" in tid else tid
        # collapse RDS<n> into 'RDS', GH<n> into 'GH', etc.
        family = "".join(ch for ch in prefix if not ch.isdigit())
        prefix_counts[family or "?"] += 1
    # On-disk task directories
    tasks_dir = REPO / "tasks"
    on_disk = sorted(p.name for p in tasks_dir.iterdir() if p.is_dir())
    families_on_disk: dict[str, int] = defaultdict(int)
    for name in on_disk:
        prefix = name.split("_")[0] if "_" in name else name
        family = "".join(ch for ch in prefix if not ch.isdigit())
        # strip seed suffix (..._seed0)
        family = family.removesuffix("seed")
        families_on_disk[family or "?"] += 1
    return {
        "source_dataset": str(ds_path.relative_to(REPO)),
        "n_dataset_entries": len(ds),
        "by_category": dict(sorted(cat_counts.items(), key=lambda x: -x[1])),
        "by_difficulty": dict(diff_counts),
        "family_counts_dataset": dict(sorted(prefix_counts.items(), key=lambda x: -x[1])),
        "n_task_dirs_on_disk": len(on_disk),
        "family_counts_on_disk": dict(sorted(families_on_disk.items(), key=lambda x: -x[1])),
        "comment": (
            "n_dataset_entries is the number of unique task templates registered in "
            "shared/teambench_dataset.json. n_task_dirs_on_disk includes seed-expanded "
            "copies (e.g., DS45_structural_break_seed0, _seed1, _seed2)."
        ),
    }


# ---------- 4. lb100 leaderboard refresh -------------------------------------

def refresh_leaderboard() -> dict:
    """Scan shared/ablation_results/lb100_*.json and produce a per-model,
    per-condition pass-rate table with cell completion percentages.
    """
    lb_dir = SHARED / "ablation_results"
    files = sorted(lb_dir.glob("lb100_*.json"))
    by_model: dict[str, dict[str, list[bool]]] = defaultdict(lambda: defaultdict(list))
    files_used = []
    for f in files:
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        # Pull model identifier
        model = d.get("model") or f.stem.replace("lb100_", "").split("_")[0]
        # Heuristic clean-up of model id
        model = str(model)
        for run in d.get("runs") or []:
            cond = (run.get("condition") or "").lower()
            if not cond:
                continue
            by_model[model][cond].append(bool(run.get("pass")))
        files_used.append(str(f.relative_to(REPO)))

    table_rows = []
    for model, by_cond in sorted(by_model.items()):
        row = {"model": model, "by_condition": {}}
        for cond, vs in by_cond.items():
            n = len(vs)
            k = sum(vs)
            lo, hi = _wilson(k, n)
            row["by_condition"][cond] = {
                "n": n,
                "passed": k,
                "rate": k / n if n else None,
                "wilson_low": lo,
                "wilson_high": hi,
            }
        table_rows.append(row)
    return {
        "files": files_used,
        "n_files": len(files_used),
        "rows": table_rows,
    }


def main() -> int:
    out = {
        "quintile_solo_stratified": recompute_quintile_solo(),
        "evaluator_confusion": recompute_evaluator_confusion(),
        "pool_composition": recompute_pool_composition(),
        "lb100_snapshot": refresh_leaderboard(),
    }
    # Write each block separately for easy paper inclusion
    (PAPER / "quintile_solo_stratified.json").write_text(
        json.dumps(out["quintile_solo_stratified"], indent=2) + "\n"
    )
    (PAPER / "evaluator_confusion.json").write_text(
        json.dumps(out["evaluator_confusion"], indent=2) + "\n"
    )
    (PAPER / "full_pool_composition.json").write_text(
        json.dumps(out["pool_composition"], indent=2) + "\n"
    )
    (PAPER / "lb100_snapshot.json").write_text(
        json.dumps(out["lb100_snapshot"], indent=2) + "\n"
    )
    # Print short report for the operator
    q = out["quintile_solo_stratified"]
    print("=== Solo-stratified quintile uplift ===")
    for row in q.get("quintiles", []):
        print(
            f"  Q{row['quintile']} (Solo {row['solo_min']:.2f}-{row['solo_max']:.2f}, "
            f"n={row['n']}): {row['mean_uplift_pp']:+.1f}pp "
            f"[{row['ci95_low_pp']:+.1f}, {row['ci95_high_pp']:+.1f}]"
        )
    e = out["evaluator_confusion"]
    print("\n=== Evaluator confusion ===")
    print(
        f"  n_runs_with_attestation={e['n_runs_with_attestation']} (of {e['n_runs_total']})"
    )
    cm = e["confusion_matrix"]
    print(
        f"  TP={cm['true_positive']}  FP(false-accept)={cm['false_positive_false_accept']}  "
        f"TN={cm['true_negative']}  FN(false-reject)={cm['false_negative_false_reject']}"
    )
    if e["false_accept_rate"] is not None:
        lo, hi = e["false_accept_ci95"]
        print(
            f"  False-accept rate: {e['false_accept_rate']*100:.1f}% "
            f"[{lo*100:.1f}, {hi*100:.1f}] over n={e['n_grader_fail_pool']} grader-fail runs"
        )
    if e["false_reject_rate"] is not None:
        lo, hi = e["false_reject_ci95"]
        print(
            f"  False-reject rate: {e['false_reject_rate']*100:.1f}% "
            f"[{lo*100:.1f}, {hi*100:.1f}] over n={e['n_grader_pass_pool']} grader-pass runs"
        )
    p = out["pool_composition"]
    print("\n=== Pool composition ===")
    print(f"  dataset entries: {p['n_dataset_entries']}, on-disk task dirs: {p['n_task_dirs_on_disk']}")
    print(f"  by_difficulty: {p['by_difficulty']}")
    lb = out["lb100_snapshot"]
    print(f"\n=== lb100 snapshot ({lb['n_files']} files) ===")
    for row in lb["rows"]:
        cells = []
        for c, info in row["by_condition"].items():
            cells.append(f"{c}:{info['passed']}/{info['n']}")
        print(f"  {row['model']}: {' '.join(cells)}")
    print(f"\nWrote 4 JSONs to {PAPER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
