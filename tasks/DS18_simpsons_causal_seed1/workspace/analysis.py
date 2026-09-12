"""
Causal inference for effect of university prestige on job performance.
BUG: Conditions on the COLLIDER variable (hired) when estimating the
treatment effect. This introduces collider bias (Berkson's paradox), opening
a spurious backdoor path and biasing the estimate.

The causal DAG: SES -> top_university AND performance (confounder). University AND performance -> hired (collider).

Rules:
- ADJUST for confounders (block backdoor paths from treatment to outcome)
- DO NOT adjust for colliders (conditioning opens non-causal paths)

Fix: Include ONLY socioeconomic_status as a control variable, NOT hired.
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/causal_data.csv")

treatment = "top_university"
outcome = "job_performance"
confounder = "socioeconomic_status"
collider = "hired"

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
