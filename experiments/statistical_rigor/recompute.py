#!/usr/bin/env python3
"""
Statistical rigor pass for paper headline claims.

For each category in the regression dataset:
  - Mean uplift (full - oracle) with 95% bootstrap CI
  - Wilson CI on pass-rate (full)
  - Paired test (t-test) p-value
  - Holm-Bonferroni adjusted p across categories
  - Post-hoc power for the observed effect at alpha=0.05

Reads:
  shared/paper/task_regression_data.csv

Writes:
  shared/paper/statistical_rigor.json
  shared/paper/table_statistical_rigor.tex
"""
from __future__ import annotations
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "shared" / "paper" / "task_regression_data.csv"


def wilson_ci(x: int, n: int, z: float = 1.96):
    if n == 0:
        return (0.0, 0.0)
    p = x / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    halfw = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return max(0.0, centre - halfw), min(1.0, centre + halfw)


def bootstrap_mean_ci(vals, n_boot=2000, seed=42):
    rng = np.random.default_rng(seed)
    a = np.asarray(vals, dtype=float)
    n = len(a)
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    m = float(a.mean())
    resample = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        resample[i] = a[idx].mean()
    return m, float(np.percentile(resample, 2.5)), float(np.percentile(resample, 97.5))


def holm_bonferroni(pvals):
    """Return adjusted p-values, preserving order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        val = min(1.0, pvals[i] * (m - rank))
        running = max(running, val)
        adj[i] = running
    return adj


def post_hoc_power_paired(effect, n, sd, alpha=0.05):
    """Rough power for a paired t-test: one-sided at alpha."""
    if sd <= 0 or n < 2:
        return float("nan")
    d = effect / sd
    nc = d * math.sqrt(n)
    crit = stats.t.ppf(1 - alpha, df=n - 1)
    return float(1.0 - stats.nct.cdf(crit, df=n - 1, nc=nc))


def main() -> int:
    groups_uplift: dict[str, list[float]] = defaultdict(list)
    groups_oracle: dict[str, list[float]] = defaultdict(list)
    groups_full: dict[str, list[float]] = defaultdict(list)
    with CSV_PATH.open() as f:
        for r in csv.DictReader(f):
            try:
                cat = r["category"]
                oracle = float(r["oracle"])
                full = float(r["full"])
            except (ValueError, KeyError):
                continue
            groups_uplift[cat].append(full - oracle)
            groups_oracle[cat].append(oracle)
            groups_full[cat].append(full)

    rows, raw_ps = [], []
    for cat, up in sorted(groups_uplift.items()):
        n = len(up)
        mean, lo, hi = bootstrap_mean_ci(up)
        arr = np.asarray(up)
        sd = float(arr.std(ddof=1)) if n > 1 else 0.0
        if n > 1 and sd > 0:
            t, p = stats.ttest_rel(groups_full[cat], groups_oracle[cat])
            p = float(p)
        else:
            p = float("nan")
        pass_full = int(sum(1 for v in groups_full[cat] if v >= 0.8))
        wlo, whi = wilson_ci(pass_full, n)
        power = post_hoc_power_paired(mean, n, sd)
        rows.append({
            "category": cat, "n": n,
            "uplift_mean": mean, "uplift_ci95": [lo, hi],
            "raw_p": p, "pass_rate_full": pass_full / n if n else 0.0,
            "pass_rate_full_wilson_ci95": [wlo, whi],
            "post_hoc_power": power, "sd_uplift": sd,
        })
        raw_ps.append(p if not math.isnan(p) else 1.0)

    adj_ps = holm_bonferroni(raw_ps)
    for row, adj in zip(rows, adj_ps):
        row["holm_adj_p"] = adj
        row["sig_after_correction"] = adj < 0.05

    # Overall claim: mean uplift across all tasks
    all_up = [u for vs in groups_uplift.values() for u in vs]
    overall_mean, overall_lo, overall_hi = bootstrap_mean_ci(all_up)
    t_all, p_all = stats.ttest_1samp(all_up, 0.0) if len(all_up) > 1 else (float("nan"), float("nan"))

    result = {
        "overall": {
            "n": len(all_up),
            "mean_uplift": overall_mean,
            "ci95": [overall_lo, overall_hi],
            "p_value": float(p_all),
        },
        "by_category": rows,
        "method": "Holm-Bonferroni across categories, bootstrap=2000, Wilson CIs on rates.",
    }
    out_json = ROOT / "shared" / "paper" / "statistical_rigor.json"
    out_json.write_text(json.dumps(result, indent=2))

    lines = [
        r"\begin{table}[h]\centering\small",
        r"\caption{Per-category team uplift with multiplicity correction. "
        r"$\Delta$ is mean (full $-$ oracle). Bootstrap 95\% CI. Raw and "
        r"Holm-adjusted $p$-values from paired $t$-test. Significance uses "
        r"$\alpha=0.05$ on adjusted $p$.}",
        r"\label{tab:stat_rigor}",
        r"\begin{tabular}{lcccccc}\toprule",
        r"Category & $n$ & $\Delta$ & 95\% CI & $p_{\text{raw}}$ & $p_{\text{Holm}}$ & Power \\ \midrule",
    ]
    for row in rows:
        lo, hi = row["uplift_ci95"]
        mark = r"$^{*}$" if row["sig_after_correction"] else ""
        lines.append(
            f"{row['category'].replace('_', ' ')} & {row['n']} & "
            f"{row['uplift_mean']:+.3f}{mark} & [{lo:+.3f}, {hi:+.3f}] & "
            f"{row['raw_p']:.3f} & {row['holm_adj_p']:.3f} & {row['post_hoc_power']:.2f} \\\\"
        )
    lines.append(r"\midrule")
    lines.append(
        f"Overall & {result['overall']['n']} & {overall_mean:+.3f} & "
        f"[{overall_lo:+.3f}, {overall_hi:+.3f}] & {p_all:.3f} & -- & -- \\\\"
    )
    lines.append(r"\bottomrule\end{tabular}\end{table}")
    out_tex = ROOT / "shared" / "paper" / "table_statistical_rigor.tex"
    out_tex.write_text("\n".join(lines))

    print(f"wrote {out_json}")
    print(f"wrote {out_tex}")
    print(f"overall mean uplift: {overall_mean:+.3f} CI=[{overall_lo:+.3f}, {overall_hi:+.3f}] "
          f"p={p_all:.3f} (n={len(all_up)})")
    for row in rows:
        star = "*" if row["sig_after_correction"] else " "
        print(f"  {star} {row['category']:18s} n={row['n']:3d} uplift={row['uplift_mean']:+.3f} "
              f"p_raw={row['raw_p']:.3f} p_holm={row['holm_adj_p']:.3f} "
              f"power={row['post_hoc_power']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
