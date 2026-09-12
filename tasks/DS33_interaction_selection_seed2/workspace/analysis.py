"""
Interaction feature selection for medical cost prediction with interaction features.
BUG: Generates ALL pairwise interaction features without any selection.
With 5 features this creates 10 interactions,
most of which are noise. Including all interactions overfits and inflates
apparent R^2 through spurious correlations.

Fix: Use partial F-test with Bonferroni correction to select only
statistically significant interactions.
alpha_bonferroni = 0.05 / n_interactions
For each candidate interaction, test if adding it significantly reduces
residual sum of squares (F-test comparing nested models).
"""
import pandas as pd
import numpy as np
import json
from itertools import combinations

df = pd.read_csv("data/features.csv")
target_col = "log_cost"
features = ['age', 'bmi', 'smoker', 'num_claims', 'chronic_conditions']

X_base = df[features].values
y = df[target_col].values
n, p = X_base.shape

# Generate ALL pairwise interactions (BUG: no selection)
interaction_names = []
interaction_cols = []
for f1, f2 in combinations(features, 2):
    col = df[f1].values * df[f2].values
    interaction_names.append(f"{f1}_x_{f2}")
    interaction_cols.append(col)

# BUG: include ALL interactions without testing significance
X_full = np.column_stack([np.ones(n), X_base] + interaction_cols)

# Fit model with all interactions
coef, _, _, _ = np.linalg.lstsq(X_full, y, rcond=None)
y_pred = X_full @ coef
ss_res = np.sum((y - y_pred)**2)
ss_tot = np.sum((y - y.mean())**2)
r2_biased = 1 - ss_res / ss_tot

results = {
    "n_interactions_used": len(interaction_names),  # BUG: all of them
    "selected_interactions": interaction_names,       # BUG: no selection
    "bonferroni_alpha": None,  # BUG: not applied
    "r2": float(r2_biased),
    "method": "all_interactions",  # BUG: should be "bonferroni_selected"
    "n_samples": n,
    "n_features_base": p,
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"All {len(interaction_names)} interactions included (no selection) — overfitting likely!")
print(f"R2 (biased by inclusion of all): {r2_biased:.4f}")
print("Saved results.json")
