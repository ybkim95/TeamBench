"""
Regression Discontinuity analysis for regression discontinuity at loan approval credit cutoff.
BUG 1: Uses arbitrary bandwidth (half the running variable range) instead of
the IK-optimal bandwidth.
BUG 2: Does not run McCrary density test to check for manipulation at the cutoff.
BUG 3: Uses simple mean difference (not local linear regression) within window.

Fix:
1. Compute IK-optimal bandwidth: h = 2.702 * std(running_var) * n^(-0.2)
2. Run McCrary density test: compare density of running variable just below and
   just above the cutoff (use a histogram or kernel density comparison)
3. Use LOCAL LINEAR regression (not mean difference) within the bandwidth
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/rd_data.csv")
running_var = "credit_score"
outcome = "default_rate"
treatment = "approved"
cutoff = 507.6

# BUG: arbitrary bandwidth (1/4 of range) instead of IK-optimal
r_range = df[running_var].max() - df[running_var].min()
bandwidth = r_range / 4  # BUG: arbitrary

# Subset to window
window = df[abs(df[running_var] - cutoff) <= bandwidth]

# BUG: simple mean difference, not local linear regression
treated_mean = window[window[treatment] == 1][outcome].mean()
control_mean = window[window[treatment] == 0][outcome].mean()
rd_effect = treated_mean - control_mean

results = {
    "rd_effect": float(rd_effect),
    "bandwidth": float(bandwidth),
    "bandwidth_method": "arbitrary",  # BUG: should be "IK_optimal"
    "n_in_window": len(window),
    "cutoff": cutoff,
    "mccrary_test": None,  # BUG: not computed
    "method": "mean_difference",  # BUG: should be "local_linear"
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"RD effect (naive): {rd_effect:.4f}")
print(f"Bandwidth (arbitrary): {bandwidth:.4f}")
print("WARNING: Using arbitrary bandwidth and naive estimator!")
print("Saved results.json")
