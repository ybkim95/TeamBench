"""
Cohort retention matrix for mobile app user retention analysis.
BUG 1: Includes right-truncated cohorts (incomplete observation window) in all
       period calculations, deflating retention rates for later periods.
BUG 2: Does not exclude the anomalous cohort (data quality issue) which has
       anomalously low retention due to a system bug.

Fix:
1. Identify and exclude cohorts where observation window < n_periods
2. Exclude cohorts with anomalously low period-1 retention (< 0.20)
3. Recompute retention matrix on clean cohorts only
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/cohort_events.csv")
n_periods = 6

cohorts = df["install_month"].unique()
cohorts = sorted(cohorts)

# BUG: does not check for truncated cohorts or exclude anomalous cohort
# All cohorts are used regardless of observation window completeness

retention_matrix = {}
for cohort in cohorts:
    cdf = df[(df["install_month"] == cohort) & (df["period"] == 0)]
    cohort_size = len(cdf)
    if cohort_size == 0:
        continue
    row = {}
    for p in range(n_periods + 1):
        active = df[(df["install_month"] == cohort) & (df["period"] == p)]["active"].sum()
        # BUG: uses full cohort_size denominator even for truncated cohorts
        row[f"period_{p}"] = round(active / cohort_size, 4)
    retention_matrix[cohort] = row

# BUG: averages include truncated and anomalous cohorts
avg_retention = {}
for p in range(n_periods + 1):
    vals = [v.get(f"period_{p}", np.nan) for v in retention_matrix.values()]
    vals = [x for x in vals if not np.isnan(x)]
    avg_retention[f"period_{p}"] = round(np.mean(vals), 4) if vals else 0.0

results = {
    "cohorts_included": list(retention_matrix.keys()),
    "n_cohorts_used": len(retention_matrix),   # BUG: should exclude truncated/anomalous
    "excluded_truncated": False,                # BUG: should be True
    "excluded_anomalous": False,                # BUG: should be True
    "avg_retention": avg_retention,
    "retention_matrix": retention_matrix,
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Cohorts used: {len(retention_matrix)} (WARNING: includes truncated/anomalous)")
print(f"Avg period-1 retention: {avg_retention.get('period_1', 0):.4f} (may be deflated)")
