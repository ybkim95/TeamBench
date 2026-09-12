"""Verifier confusion matrix on the complete 27-config x 3-seed dataset.

Pairs the verifier's attestation verdict against the deterministic grader's
pass field, broken down by Verifier provider family. Dedups by
(config, task, seed); duplicates from parallel-worker overlap have already
been collapsed.

Writes shared/paper/evaluator_confusion_recomputed.json in the schema that
paper/scripts/error_analysis_fig.py expects, then prints a summary table.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path("/u/ybkim95/TeamBench")
PER_RUN = ROOT / "shared" / "role_ablation" / "results" / "per_run.jsonl"
OUT_JSON = ROOT / "shared" / "paper" / "evaluator_confusion_recomputed.json"

# Map config letter -> family label that the figure script keys on
PROVIDER_LABEL = {
    "A": "Anthropic (Haiku-4.5)",
    "G": "Google (Gemini-3 Flash)",
    "O": "OpenAI (GPT-5.4 Mini)",
}
PROVIDER_SHORT = {"A": "Haiku-4.5", "G": "Gem-3f", "O": "GPT-5.4m"}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


# Dedup by (config, task, seed): latest record wins
cells: dict[tuple[str, str, int], dict] = {}
with PER_RUN.open() as f:
    for line in f:
        r = json.loads(line)
        if "ImportError" in (r.get("error") or ""):
            continue
        cfg, task, seed = r.get("config"), r.get("task_id"), r.get("seed")
        if cfg is None or task is None or seed is None:
            continue
        cells[(cfg, task, int(seed))] = r

# Per-provider confusion bucketed by Verifier letter
per_prov_raw = defaultdict(lambda: {"TP": 0, "FP": 0, "FN": 0, "TN": 0,
                                     "total": 0, "missing": 0})
for (cfg, _t, _s), r in cells.items():
    verifier_letter = cfg[5]  # P{X}E{Y}V{Z}
    bucket = per_prov_raw[verifier_letter]
    bucket["total"] += 1
    grader_pass = bool(r.get("pass"))
    run_dir = Path(r.get("run_dir") or "")
    att = run_dir / "submission" / "attestation.json"
    if not att.exists():
        bucket["missing"] += 1
        continue
    try:
        attest = json.loads(att.read_text())
    except Exception:
        bucket["missing"] += 1
        continue
    v = (attest.get("verdict") or "").lower()
    verifier_pass = v in ("pass", "passed", "ok")
    if verifier_pass and grader_pass:
        bucket["TP"] += 1
    elif verifier_pass and not grader_pass:
        bucket["FP"] += 1
    elif not verifier_pass and not grader_pass:
        bucket["TN"] += 1
    else:
        bucket["FN"] += 1


def to_provider_dict(b: dict) -> dict:
    n_att = b["TP"] + b["FP"] + b["FN"] + b["TN"]
    n_grader_fail = b["FP"] + b["TN"]
    n_grader_pass = b["TP"] + b["FN"]
    fa = b["FP"] / n_grader_fail if n_grader_fail else 0.0
    fr = b["FN"] / n_grader_pass if n_grader_pass else 0.0
    accuracy = (b["TP"] + b["TN"]) / n_att if n_att else 0.0
    return {
        "total": b["total"],
        "missing": b["missing"],
        "with_attestation": n_att,
        "TP": b["TP"], "FP": b["FP"], "FN": b["FN"], "TN": b["TN"],
        "false_accept_rate": fa,
        "false_reject_rate": fr,
        "accuracy": accuracy,
    }


per_prov_out = {PROVIDER_LABEL[letter]: to_provider_dict(per_prov_raw[letter])
                for letter in "AGO"}

# Pooled
pooled = {"TP": 0, "FP": 0, "FN": 0, "TN": 0, "missing": 0, "total": 0}
for letter in "AGO":
    for k, v in per_prov_raw[letter].items():
        pooled[k] += v
n_att = pooled["TP"] + pooled["FP"] + pooled["FN"] + pooled["TN"]
n_grader_fail = pooled["FP"] + pooled["TN"]
n_grader_pass = pooled["TP"] + pooled["FN"]
fa = pooled["FP"] / n_grader_fail if n_grader_fail else 0.0
fr = pooled["FN"] / n_grader_pass if n_grader_pass else 0.0
fa_lo, fa_hi = wilson(pooled["FP"], n_grader_fail)
fr_lo, fr_hi = wilson(pooled["FN"], n_grader_pass)

doc = {
    "source": "shared/role_ablation/results/per_run.jsonl (dedup latest per config,task,seed; full 27x25x3 grid)",
    "n_runs_unique": len(cells),
    "n_runs_with_attestation": n_att,
    "n_runs_missing_attestation": pooled["missing"],
    "confusion_matrix": {
        "true_positive": pooled["TP"],
        "false_positive_false_accept": pooled["FP"],
        "true_negative": pooled["TN"],
        "false_negative_false_reject": pooled["FN"],
    },
    "false_accept_rate": fa,
    "false_accept_ci95": [fa_lo, fa_hi],
    "false_reject_rate": fr,
    "false_reject_ci95": [fr_lo, fr_hi],
    "per_provider": per_prov_out,
}

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(doc, indent=2) + "\n")

# Print summary
print(f"Total unique cells: {len(cells)}")
print()
print(f"{'Provider':<25}{'TP':>5}{'FP':>5}{'FN':>5}{'TN':>5}{'n_att':>8}"
      f"{'FA':>10}{'FR':>10}")
print("-" * 75)
for letter in "AGO":
    p = per_prov_out[PROVIDER_LABEL[letter]]
    print(f"{PROVIDER_LABEL[letter]:<25}{p['TP']:>5}{p['FP']:>5}"
          f"{p['FN']:>5}{p['TN']:>5}{p['with_attestation']:>8}"
          f"  {p['false_accept_rate']*100:>5.1f}%"
          f"  {p['false_reject_rate']*100:>5.1f}%")
print("-" * 75)
print(f"{'POOLED':<25}{pooled['TP']:>5}{pooled['FP']:>5}{pooled['FN']:>5}"
      f"{pooled['TN']:>5}{n_att:>8}  {fa*100:>5.1f}%  {fr*100:>5.1f}%")
print()
print(f"Wrote {OUT_JSON}")
