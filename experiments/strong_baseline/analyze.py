#!/usr/bin/env python3
"""
Strong-baseline analysis: recompute oracle vs oracle_cot vs oracle_2pass vs full team
on the 28-task cross-model subset (gemini-3-flash-preview, seed 0).

Reads:
  shared/ablation_results/strong_baseline_{model}_seed0.json   -> oracle_cot, oracle_2pass runs
  shared/ablation_results/crossmodel_{model}_seed0.json        -> oracle, restricted, full, ... runs

Writes:
  shared/paper/strong_baseline_comparison.json
  shared/paper/table_strong_baseline_v2.tex

Claim under test: a scaffolded single agent does not close the gap to a full team.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from harness.statistics import bootstrap_ci, bootstrap_ci_difference, mcnemar_test


MODEL_PAIRS = [
    # (friendly_name, strong_baseline_file_stem, crossmodel_file_stem)
    ("gemini-3-flash-preview",
     "strong_baseline_gemini3flashpreview_seed0",
     "crossmodel_g3flash_seed0"),
    # Extend here once strong-baseline is run on Claude/GPT.
]

CROSSMODEL_CONDITIONS = ["oracle", "restricted", "team_no_plan", "team_no_verify", "full"]
STRONG_CONDITIONS = ["oracle_cot", "oracle_2pass"]


def load_runs(path: Path) -> List[dict]:
    if not path.exists():
        return []
    with path.open() as f:
        return json.load(f).get("runs", [])


def pivot_by_task(runs: List[dict], conditions: List[str]) -> Dict[str, Dict[str, float]]:
    """task_id -> condition -> partial_score (last seed if multiple)."""
    out: Dict[str, Dict[str, float]] = {}
    for r in runs:
        cond = r.get("condition")
        if cond not in conditions:
            continue
        out.setdefault(r["task_id"], {})[cond] = float(r.get("partial_score", 0.0))
    return out


def analyse_model(friendly: str, strong_stem: str, crossmodel_stem: str) -> dict:
    strong_path = ROOT / "shared" / "ablation_results" / f"{strong_stem}.json"
    cross_path = ROOT / "shared" / "ablation_results" / f"{crossmodel_stem}.json"
    strong = pivot_by_task(load_runs(strong_path), STRONG_CONDITIONS)
    cross = pivot_by_task(load_runs(cross_path), CROSSMODEL_CONDITIONS)

    tasks = sorted(set(strong) & set(cross))
    if not tasks:
        return {"model": friendly, "error": "no overlapping tasks", "n": 0}

    vec = {c: [] for c in CROSSMODEL_CONDITIONS + STRONG_CONDITIONS}
    for t in tasks:
        for c in CROSSMODEL_CONDITIONS:
            vec[c].append(cross[t].get(c, 0.0))
        for c in STRONG_CONDITIONS:
            vec[c].append(strong[t].get(c, 0.0))
    arr = {c: np.asarray(v, dtype=float) for c, v in vec.items()}

    def summary(c: str) -> dict:
        scores = arr[c]
        passes = (scores >= 0.8).astype(int).tolist()
        # bootstrap_ci returns (mean, lo, hi); works on 0/1 or float in [0,1]
        _, mean_lo, mean_hi = bootstrap_ci(scores.tolist())
        _, sr_lo, sr_hi = bootstrap_ci(passes)
        return {
            "n": len(scores),
            "mean_partial": float(scores.mean()),
            "mean_partial_ci95": [mean_lo, mean_hi],
            "success_rate": float(np.mean(passes)),
            "success_rate_ci95": [sr_lo, sr_hi],
        }

    per_cond = {c: summary(c) for c in CROSSMODEL_CONDITIONS + STRONG_CONDITIONS}

    contrasts: Dict[str, dict] = {}
    for baseline in ("oracle", "oracle_cot", "oracle_2pass"):
        if baseline not in arr:
            continue
        diff = arr["full"] - arr[baseline]
        _, lo, hi = bootstrap_ci_difference(arr["full"].tolist(), arr[baseline].tolist())
        full_pass = (arr["full"] >= 0.8).astype(int)
        base_pass = (arr[baseline] >= 0.8).astype(int)
        _, mc_p = mcnemar_test(full_pass.tolist(), base_pass.tolist())
        contrasts[f"full_vs_{baseline}"] = {
            "mean_delta": float(diff.mean()),
            "mean_delta_ci95": [lo, hi],
            "sig": lo > 0 or hi < 0,
            "mcnemar_p": float(mc_p),
        }

    return {
        "model": friendly,
        "n_tasks": len(tasks),
        "tasks": tasks,
        "per_condition": per_cond,
        "contrasts": contrasts,
    }


def write_latex(results: List[dict], out_path: Path) -> None:
    results = [r for r in results if "per_condition" in r]
    rows = []
    rows.append(r"\begin{table}[h]\centering\small")
    rows.append(r"\caption{Full team vs.\ strong single-agent baselines. Scaffolded "
                r"oracles (CoT, two-pass) do not close the gap to a team. "
                r"$\Delta$ is full minus baseline mean partial score; "
                r"95\% CIs via bootstrap ($B=2000$).}")
    rows.append(r"\label{tab:strong_baseline}")
    rows.append(r"\begin{tabular}{llcccc}\toprule")
    rows.append(r"Model & Baseline & Mean & Full & $\Delta$ & 95\% CI \\ \midrule")
    for r in results:
        model = r["model"].replace("_", r"\_")
        full_mean = r["per_condition"]["full"]["mean_partial"]
        for base in ("oracle", "oracle_cot", "oracle_2pass"):
            if base not in r["per_condition"]:
                continue
            base_mean = r["per_condition"][base]["mean_partial"]
            con = r["contrasts"][f"full_vs_{base}"]
            lo, hi = con["mean_delta_ci95"]
            star = r"\textbf{}" if con["sig"] else ""
            rows.append(
                f"{model} & {base.replace('_', ' ')} & {base_mean:.3f} & {full_mean:.3f} & "
                f"{con['mean_delta']:+.3f}{star} & [{lo:+.3f}, {hi:+.3f}] \\\\"
            )
    rows.append(r"\bottomrule\end{tabular}\end{table}")
    out_path.write_text("\n".join(rows))


def main() -> int:
    results = [analyse_model(*p) for p in MODEL_PAIRS]
    out_json = ROOT / "shared" / "paper" / "strong_baseline_comparison.json"
    out_json.write_text(json.dumps(results, indent=2))
    out_tex = ROOT / "shared" / "paper" / "table_strong_baseline_v2.tex"
    write_latex(results, out_tex)
    print(f"wrote {out_json}")
    print(f"wrote {out_tex}")
    for r in results:
        if "error" in r:
            print(f"  {r['model']}: {r['error']}")
            continue
        pc = r["per_condition"]
        print(f"\n{r['model']} (n={r['n_tasks']})")
        for c in ["oracle", "oracle_cot", "oracle_2pass", "full"]:
            if c in pc:
                print(f"  {c:14s} mean={pc[c]['mean_partial']:.3f}  "
                      f"sr={pc[c]['success_rate']:.3f}  "
                      f"CI=[{pc[c]['mean_partial_ci95'][0]:.3f}, {pc[c]['mean_partial_ci95'][1]:.3f}]")
        for name, con in r["contrasts"].items():
            lo, hi = con["mean_delta_ci95"]
            print(f"  {name:25s} delta={con['mean_delta']:+.3f}  CI=[{lo:+.3f},{hi:+.3f}]  "
                  f"mcnemar_p={con['mcnemar_p']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
