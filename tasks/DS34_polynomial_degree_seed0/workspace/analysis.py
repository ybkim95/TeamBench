"""
Polynomial feature engineering for drug dose-response curve with selective polynomial expansion.
BUG: Applies degree-3 polynomial expansion to ALL features uniformly.
This generates ~34 polynomial features for 4 inputs, most of which
are noise from linear features. Overfits and loses interpretability.

Fix:
1. Test each feature for nonlinearity using F-test (compare linear vs quadratic)
2. Apply degree-2 expansion ONLY to features with significant nonlinearity (p < 0.05)
3. Keep linear features as-is
"""
import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import PolynomialFeatures

df = pd.read_csv("data/features.csv")
target_col = "effect_size"
features = ['patient_age', 'body_weight', 'dose_mg', 'concentration']

X = df[features].values
y = df[target_col].values
n = len(X)

# BUG: degree-3 expansion on ALL features without selection
poly = PolynomialFeatures(degree=3, include_bias=False)
X_poly = poly.fit_transform(X)

coef, _, _, _ = np.linalg.lstsq(
    np.column_stack([np.ones(n), X_poly]), y, rcond=None
)
y_pred = np.column_stack([np.ones(n), X_poly]) @ coef
ss_res = float(np.sum((y - y_pred)**2))
ss_tot = float(np.sum((y - y.mean())**2))
r2 = 1 - ss_res / ss_tot

results = {
    "degree_used": 3,                # BUG: should be selective
    "expansion_method": "all_features_degree3",  # BUG: should be "selective"
    "n_poly_features": X_poly.shape[1],
    "nonlinear_features_detected": [],  # BUG: not tested
    "linear_features_kept": [],         # BUG: not tested
    "r2": float(r2),
    "n_samples": n,
    "nonlinearity_test_applied": False,  # BUG
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Degree-3 expansion: {X_poly.shape[1]} features from {len(features)} inputs (no selection)")
print(f"R2: {r2:.4f}")
print("WARNING: All features expanded to degree 3 — likely overfitting!")
print("Saved results.json")
