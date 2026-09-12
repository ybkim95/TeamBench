"""
Time series forecast for weekly website traffic with structural break.
BUG: Fits a single linear trend across the ENTIRE series, ignoring a structural
break in the data. When the series has a break (e.g., sudden acceleration in
growth due to a product launch or market event), a single trend model will:
- Under-fit the post-break period (positive break: forecast too low)
- Blend two different regimes into one poor estimate

Fix:
1. Detect the structural break using a Chow test (test all candidate breakpoints,
   pick the one that minimizes the combined RSS of two separate OLS fits)
2. Fit separate OLS models for pre-break and post-break periods
3. Use the post-break model for forecasting
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/time_series.csv")
n = len(df)

# BUG: single OLS fit ignores structural break
t = df["period"].values
y = df["weekly_sessions"].values

# Single linear regression
t_mean = t.mean()
y_mean = y.mean()
slope = np.sum((t - t_mean) * (y - y_mean)) / np.sum((t - t_mean)**2)
intercept = y_mean - slope * t_mean

# BUG: forecasts using single trend (will be biased if break exists)
forecast_next = intercept + slope * (n + 1)
fitted = intercept + slope * t
residuals = y - fitted
rmse = np.sqrt(np.mean(residuals**2))

results = {
    "n_periods": n,
    "model": "single_ols",           # BUG: should be "piecewise_ols"
    "break_detected": False,          # BUG: should be True
    "break_point": None,              # BUG: should be detected break point
    "forecast_next_period": round(float(forecast_next), 2),
    "rmse": round(float(rmse), 4),
    "slope": round(float(slope), 4),
    "intercept": round(float(intercept), 4),
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Forecast (single trend): {forecast_next:.2f}")
print(f"RMSE: {rmse:.4f} (WARNING: single trend ignores structural break)")
