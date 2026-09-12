#!/usr/bin/env python3
"""
Equalizer-effect replication across models: re-compute the Pearson correlation
between oracle score and team uplift (full - oracle) per-task, for every model
with 5-condition cross-model data.

Reads:
  shared/ablation_results/crossmodel_*.json

Writes:
  shared/paper/equalizer_replication.json
  shared/paper/table_equalizer_replication.tex

Claim under test: r(oracle, uplift) < 0 and consistent across model providers.
"""
from __future__ import annotations
import glob
import json
import math
from pathlib import Path
from typing import Dict, List

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
GLOB = str(ROOT / "shared" / "ablation_results" / "crossmodel_*_seed0.json")

SKIP_MODELS = {"crossmodel_gpt_oss_20b_seed0.json"}  # open-source failure tier


def pivot(runs: List[dict]) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    for r in runs:
        out.setdefault(r["task_id"], {})[r["condition"]] = float(r.get("partial_score", 0.0))
    return out


def pearson_ci(x: np.ndarray, y: np.ndarray, n_boot=2000, seed=42):
    if np.std(x) == 0 or np.std(y) == 0:
        return float("nan"), float("nan"), float("nan")
    r_obs, _ = stats.pearsonr(x, y)
    rng = np.random.default_rng(seed)
    rs = np.empty(n_boot)
    n = len(x)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        xi, yi = x[idx], y[idx]
        if np.std(xi) == 0 or np.std(yi) == 0:
            rs[i] = np.nan
            continue
        try:
            rs[i], _ = stats.pearsonr(xi, yi)
        except Exception:
            rs[i] = np.nan
    rs = rs[~np.isnan(rs)]
    if len(rs) < 10:
        return float(r_obs), float("nan"), float("nan")
    lo, hi = float(np.percentile(rs, 2.5)), float(np.percentile(rs, 97.5))
    return float(r_obs), lo, hi


def analyse(path: Path):
    name = path.name
    if name in SKIP_MODELS:
        return None
    with path.open() as f:
        d = json.load(f)
    runs = d.get("runs", [])
    by_task = pivot(runs)
    model = d.get("model", path.stem)
    oracle, uplift = [], []
    for t, conds in by_task.items():
        if "oracle" not in conds or "full" not in conds:
            continue
        oracle.append(conds["oracle"])
        uplift.append(conds["full"] - conds["oracle"])
    if len(oracle) < 6:
        return {"model": model, "n": len(oracle), "skipped": "too few"}
    x = np.asarray(oracle); y = np.asarray(uplift)
    if np.std(x) == 0 or np.std(y) == 0:
        return {"model": model, "n": len(oracle), "skipped": "zero variance",
                "oracle_mean": float(x.mean()), "uplift_mean": float(y.mean())}
    r, lo, hi = pearson_ci(x, y)
    rho, rho_p = stats.spearmanr(x, y)
    _, pval = stats.pearsonr(x, y)
    return {
        "model": model,
        "n": int(len(oracle)),
        "pearson_r": r,
        "pearson_ci95": [lo, hi],
        "pearson_p": float(pval),
        "spearman_rho": float(rho),
        "spearman_p": float(rho_p),
        "consistent_with_equalizer": hi < 0,
        "oracle_mean": float(x.mean()),
        "uplift_mean": float(y.mean()),
    }


def main() -> int:
    paths = sorted(Path(p) for p in glob.glob(GLOB))
    results = [r for r in (analyse(p) for p in paths) if r]

    # Meta-analysis: Fisher z-combined r across models
    zs, ws = [], []
    for r in results:
        if r.get("skipped"):
            continue
        n = r["n"]; corr = r["pearson_r"]
        if n < 4 or not (-1 < corr < 1):
            continue
        zs.append(np.arctanh(corr))
        ws.append(n - 3)
    if ws:
        z_mean = float(np.sum(np.asarray(zs) * np.asarray(ws)) / np.sum(ws))
        r_meta = float(np.tanh(z_mean))
        se = float(1.0 / math.sqrt(float(np.sum(ws))))
        lo_meta = float(np.tanh(z_mean - 1.96 * se))
        hi_meta = float(np.tanh(z_mean + 1.96 * se))
    else:
        r_meta, lo_meta, hi_meta = float("nan"), float("nan"), float("nan")

    out = {
        "per_model": results,
        "meta": {
            "fisher_r": r_meta,
            "ci95": [lo_meta, hi_meta],
            "n_models": len(ws),
            "note": "Fisher-z pooled across models with valid r.",
        },
    }
    out_json = ROOT / "shared" / "paper" / "equalizer_replication.json"
    out_json.write_text(json.dumps(out, indent=2))

    lines = [
        r"\begin{table}[h]\centering\small",
        r"\caption{Equalizer replication across models (28-task cross-model subset). "
        r"$r$ is Pearson correlation between oracle partial score and team uplift "
        r"(\texttt{full $-$ oracle}) across tasks. $r<0$ supports the equalizer "
        r"hypothesis. CI: 2000-iter bootstrap.}",
        r"\label{tab:equalizer_replicate}",
        r"\begin{tabular}{lccccc}\toprule",
        r"Model & $n$ & $r$ & 95\% CI & $p$ & Equalizer \\ \midrule",
    ]
    underscore_repl = "\\_"
    for r in results:
        if r.get("skipped"):
            continue
        flag = r"\checkmark" if r["consistent_with_equalizer"] else r"$\cdot$"
        lo, hi = r["pearson_ci95"]
        model_tex = r["model"].replace("_", underscore_repl)
        lines.append(
            f"{model_tex} & {r['n']} & {r['pearson_r']:+.3f} & "
            f"[{lo:+.3f}, {hi:+.3f}] & {r['pearson_p']:.3f} & {flag} \\\\"
        )
    lines.append(r"\midrule")
    lines.append(f"Pooled (Fisher-$z$) & -- & {r_meta:+.3f} & [{lo_meta:+.3f}, {hi_meta:+.3f}] & -- & -- \\\\")
    lines.append(r"\bottomrule\end{tabular}\end{table}")
    out_tex = ROOT / "shared" / "paper" / "table_equalizer_replication.tex"
    out_tex.write_text("\n".join(lines))

    print(f"wrote {out_json}")
    print(f"wrote {out_tex}")
    for r in results:
        if r.get("skipped"):
            continue
        lo, hi = r["pearson_ci95"]
        print(f"  {r['model']:35s} n={r['n']:2d}  r={r['pearson_r']:+.3f}  "
              f"CI=[{lo:+.3f}, {hi:+.3f}]  p={r['pearson_p']:.3f}  "
              f"equalizer={r['consistent_with_equalizer']}")
    print(f"  pooled r={r_meta:+.3f}  CI=[{lo_meta:+.3f}, {hi_meta:+.3f}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
