"""
A/B test analysis for e-commerce checkout page redesign.
BUG: No multiple comparison correction — inflated false positive rate.
Each metric tested at alpha=0.05; with 5 metrics, expected false positives > 0.
Fix: Apply Bonferroni correction (alpha / n_comparisons) for exploratory metrics.
"""
import pandas as pd
import numpy as np
from scipy import stats
import json

df = pd.read_csv("data/experiment_results.csv")
groups = ['control', 'treatment']
all_metrics = ['conversion_rate', 'avg_order_value', 'bounce_rate', 'time_on_page', 'cart_abandonment_rate']
primary_metric = "conversion_rate"
alpha = 0.05

results = {}
for metric in all_metrics:
    g0 = df[df["group"] == groups[0]][metric].astype(float)
    g1 = df[df["group"] == groups[1]][metric].astype(float)
    t_stat, p_val = stats.ttest_ind(g0, g1)

    # BUG: Uses same alpha for all metrics — no correction for multiple comparisons
    significant = p_val < alpha
    results[metric] = {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "significant": bool(significant),
        "alpha_used": alpha,  # BUG: should be bonferroni_alpha for exploratory metrics
    }
    print(f"{metric}: p={p_val:.4f}, significant={significant}")

# BUG: No Bonferroni correction applied
n_significant = sum(1 for r in results.values() if r["significant"])
print(f"\n{n_significant} metrics significant at alpha=0.05")

output = {
    "results": results,
    "bonferroni_correction_applied": False,  # BUG: should be True
    "n_comparisons": len(all_metrics),
    "alpha": alpha,
    "bonferroni_alpha": None,  # BUG: should be alpha/n_comparisons
    "primary_metric_significant": results[primary_metric]["significant"],
}
with open("analysis_results.json", "w") as f:
    json.dump(output, f, indent=2)
print("Saved analysis_results.json")
