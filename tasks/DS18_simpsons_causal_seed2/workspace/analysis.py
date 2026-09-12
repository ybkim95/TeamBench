"""
Causal inference for effect of medication adherence on symptom reduction.
BUG: Conditions on the COLLIDER variable (enrolled_in_study) when estimating the
treatment effect. This introduces collider bias (Berkson's paradox), opening
a spurious backdoor path and biasing the estimate.

The causal DAG: Baseline severity -> adherence AND symptoms (confounder). Adherence AND symptoms -> enrolled in study (collider).

Rules:
- ADJUST for confounders (block backdoor paths from treatment to outcome)
- DO NOT adjust for colliders (conditioning opens non-causal paths)

Fix: Include ONLY baseline_severity as a control variable, NOT enrolled_in_study.
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/causal_data.csv")

treatment = "full_adherence"
outcome = "symptom_reduction"
confounder = "baseline_severity"
collider = "enrolled_in_study"

# BUG: conditions on the collider — this is WRONG and introduces bias
# Subsetting to collider==1 opens a spurious path between treatment and outcome
df_subset = df[df[collider] == 1]  # BUG: do NOT condition on collider

X = np.column_stack([
    np.ones(len(df_subset)),
    df_subset[confounder].values,
    df_subset[collider].values,   # BUG: including collider as control
    df_subset[treatment].values,
])
y = df_subset[outcome].values

beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
ate_estimate = float(beta[-1])

results = {
    "ate_estimate": ate_estimate,
    "adjustment_set": [confounder, collider],  # BUG: should be [confounder] only
    "conditioned_on_collider": True,           # BUG: should be False
    "n_used": len(df_subset),
    "method": "collider_adjusted",             # BUG
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"ATE estimate (biased): {ate_estimate:.4f}")
print("WARNING: Conditioned on collider — estimate is biased!")
print("Saved results.json")
