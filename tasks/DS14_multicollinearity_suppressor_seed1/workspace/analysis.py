"""
Multicollinearity analysis for employee salary prediction.
BUG: Blindly removes ALL features with VIF > 15, including suppressor variables.
This is WRONG — a suppressor variable may have high VIF yet improve model fit
by removing noise variance shared with another predictor.
Fix: Report VIF values, fit the FULL model (all predictors), compare R^2 with
and without high-VIF features to assess whether removing them hurts performance.
Do NOT blindly drop features based solely on VIF threshold.
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/dataset.csv")

outcome = "annual_salary"
predictors = ['years_exp', 'education_years', 'skills_score', 'projects_completed', 'training_hours']

X = df[predictors]
y = df[outcome]

# Compute VIF for each predictor
def compute_vif(X_df):
    from numpy.linalg import lstsq
    vifs = {}
    cols = list(X_df.columns)
    for i, col in enumerate(cols):
        others = [c for c in cols if c != col]
        X_other = X_df[others].values
        y_col = X_df[col].values
        # Add intercept
        X_other = np.column_stack([np.ones(len(X_other)), X_other])
        coefs, _, _, _ = lstsq(X_other, y_col, rcond=None)
        y_hat = X_other @ coefs
        ss_res = np.sum((y_col - y_hat) ** 2)
        ss_tot = np.sum((y_col - y_col.mean()) ** 2)
        r2 = 1 - ss_res / max(ss_tot, 1e-9)
        vifs[col] = round(1 / max(1 - r2, 1e-9), 4)
    return vifs

vifs = compute_vif(X)
print("VIF values:", vifs)

# BUG: remove ALL features with VIF > threshold
vif_threshold = 15
keep = [c for c in predictors if vifs[c] <= vif_threshold]
print(f"Keeping features (VIF <= {vif_threshold}): {keep}")

# Fit reduced model (missing suppressor!)
X_keep = np.column_stack([np.ones(len(y))] + [X[c].values for c in keep])
y_arr = y.values
from numpy.linalg import lstsq
coefs, _, _, _ = lstsq(X_keep, y_arr, rcond=None)
y_hat = X_keep @ coefs
ss_res = np.sum((y_arr - y_hat) ** 2)
ss_tot = np.sum((y_arr - y_arr.mean()) ** 2)
r2 = float(1 - ss_res / max(ss_tot, 1e-9))

results = {
    "vif": vifs,
    "features_kept": keep,
    "features_dropped": [c for c in predictors if c not in keep],
    "r2": round(r2, 6),
    "method": "vif_drop",  # BUG: should use full model
    "vif_threshold": vif_threshold,
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"R^2 after VIF drop: {r2:.4f}")
print("Saved results.json")
