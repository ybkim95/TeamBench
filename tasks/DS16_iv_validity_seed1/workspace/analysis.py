"""
Instrumental Variable (2SLS) estimation for effect of smoking on lung function.
BUG 1: Uses BOTH instruments (cigarette_tax AND stress_score) without testing exclusion restriction.
BUG 2: Does not compute first-stage F-statistic (weak instrument test).
BUG 3: stress_score violates the exclusion restriction — it has a direct effect on fev1_score.

Fix:
1. Compute first-stage F-statistic (should be > 10 for valid instruments)
2. Use ONLY the valid instrument (cigarette_tax)
3. Report the 2SLS estimate using only the valid instrument
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/iv_data.csv")
outcome = "fev1_score"
endogenous = "cigarettes_per_day"
z_valid = "cigarette_tax"
z_invalid = "stress_score"

y = df[outcome].values
x = df[endogenous].values

# BUG: uses both instruments — invalid instrument violates exclusion restriction
Z = np.column_stack([np.ones(len(df)), df[z_valid].values, df[z_invalid].values])
X = np.column_stack([np.ones(len(df)), x])

# 2SLS using both instruments (biased due to invalid instrument)
Pz = Z @ np.linalg.inv(Z.T @ Z) @ Z.T
X_hat = Pz @ X
beta_2sls = np.linalg.inv(X_hat.T @ X) @ X_hat.T @ y

results = {
    "iv_effect": float(beta_2sls[1]),
    "instruments_used": [z_valid, z_invalid],  # BUG: should use only z_valid
    "first_stage_f": None,   # BUG: not computed
    "exclusion_test": None,  # BUG: not tested
    "method": "2sls_both_instruments",  # BUG
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"2SLS effect (biased): {beta_2sls[1]:.4f}")
print("WARNING: Using invalid instrument — exclusion restriction likely violated!")
print("Saved results.json")
