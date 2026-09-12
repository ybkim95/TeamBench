"""
Seasonal decomposition for daily retail sales with weekly and monthly seasonality.
BUG: Uses single-period STL with only the weekly period (7 days).
The monthly seasonal component (period ~30 days) is left in the residuals,
causing high residual autocorrelation at lag ~30.

Fix: Apply MSTL (iterative STL for each period):
1. Initialize: deseasonalized = y.copy()
2. For each period in [weekly_period, monthly_period]:
   a. Apply STL to deseasonalized series using this period
   b. Extract seasonal component, subtract from deseasonalized
3. Final trend from last STL iteration
4. Report residuals = y - trend - sum(all seasonal components)
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/daily_series.csv")
y = df["daily_sales"].values
n = len(y)
WEEKLY_PERIOD = 7
MONTHLY_PERIOD = 30  # BUG: this period is ignored

# BUG: single-period seasonal decomposition using only weekly period
# Simple moving average for trend (window=weekly_period)
window = WEEKLY_PERIOD
trend = np.convolve(y, np.ones(window)/window, mode='same')

# BUG: only weekly seasonal component extracted
seasonal_weekly = np.zeros(n)
for i in range(n):
    seasonal_weekly[i] = y[i] - trend[i]

# BUG: no monthly component extracted — monthly seasonality stays in residuals
residuals = y - trend - seasonal_weekly

# Residual ACF at lag 30 (will be high due to missed monthly component)
def acf(x, lag):
    n = len(x)
    mean_x = np.mean(x)
    var = np.var(x)
    if var < 1e-10:
        return 0.0
    cov = np.mean((x[:n-lag] - mean_x) * (x[lag:] - mean_x))
    return cov / var

residual_acf_30 = acf(residuals, 30)

results = {
    "n_days": n,
    "periods_used": [WEEKLY_PERIOD],              # BUG: should be [7, 30]
    "mstl_applied": False,                         # BUG: should be True
    "monthly_component_extracted": False,          # BUG: should be True
    "residual_acf_lag30": round(float(residual_acf_30), 4),
    "trend_mean": round(float(np.mean(trend)), 4),
    "seasonal_weekly_amplitude": round(float(np.std(seasonal_weekly)), 4),
    "seasonal_monthly_amplitude": 0.0,            # BUG: should be > 0
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Residual ACF at lag 30: {residual_acf_30:.4f} (WARNING: monthly component not removed)")
print(f"Periods used: {results['periods_used']}")
