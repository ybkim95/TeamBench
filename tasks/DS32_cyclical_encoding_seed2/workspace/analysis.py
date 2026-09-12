"""
Feature engineering for hourly taxi/rideshare demand prediction.
BUG: hour is used as a raw integer feature.
This treats period 23 and 0 as maximally distant when they are adjacent,
breaking the cyclic relationship and hurting model performance.

Fix: encode cyclic features using sin/cos transformation:
  sin_hour = sin(2 * pi * hour / 24)
  cos_hour = cos(2 * pi * hour / 24)

This maps the cyclic variable to a 2D unit circle where adjacent
time periods remain close regardless of wrap-around.
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/timeseries.csv")
target_col = "rides_count"
cyclic_col = "hour"
period = 24
num_cols = ['rain_mm', 'temp_celsius', 'is_holiday']

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
print(f"Integer encoding distance (23 to 0): {dist_max_0} (should be ~0.26 with sin/cos)")
print("WARNING: Raw integer encoding destroys cyclic relationship!")
print("Saved results.json")
