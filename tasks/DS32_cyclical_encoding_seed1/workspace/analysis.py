"""
Feature engineering for daily retail sales prediction by day of week.
BUG: day_of_week is used as a raw integer feature.
This treats period 6 and 0 as maximally distant when they are adjacent,
breaking the cyclic relationship and hurting model performance.

Fix: encode cyclic features using sin/cos transformation:
  sin_day_of_week = sin(2 * pi * day_of_week / 7)
  cos_day_of_week = cos(2 * pi * day_of_week / 7)

This maps the cyclic variable to a 2D unit circle where adjacent
time periods remain close regardless of wrap-around.
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/timeseries.csv")
target_col = "sales_amount"
cyclic_col = "day_of_week"
period = 7
num_cols = ['store_size', 'promotions', 'foot_traffic']

# BUG: using raw integer encoding for cyclic feature
# hour 23 and hour 0 get distance = 23, but they are only 1 step apart!
df["cyclic_encoded"] = df[cyclic_col]  # BUG: integer, not sin/cos

features = num_cols + ["cyclic_encoded"]
X = df[features].values
y = df[target_col].values

# Fit simple linear model
from numpy.linalg import lstsq
X_aug = np.column_stack([np.ones(len(X)), X])
coef, _, _, _ = lstsq(X_aug, y, rcond=None)
y_pred = X_aug @ coef
residuals = y - y_pred

# Check: distance between adjacent periods using integer encoding
dist_max_0 = abs(period - 1 - 0)  # BUG: shows period-1, should be ~0.26 with sin/cos

results = {
    "cyclic_col": cyclic_col,
    "period": period,
    "encoding_method": "integer",  # BUG: should be "sincos"
    "sin_col": None,   # BUG: not computed
    "cos_col": None,   # BUG: not computed
    "dist_period_minus1_to_0": dist_max_0,  # BUG: large integer distance
    "rmse": float(np.sqrt(np.mean(residuals**2))),
    "n_samples": len(df),
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Integer encoding distance (6 to 0): {dist_max_0} (should be ~0.26 with sin/cos)")
print("WARNING: Raw integer encoding destroys cyclic relationship!")
print("Saved results.json")
