"""
Demand forecast for electronics accessories demand with stockout censoring.
BUG: Uses OLS on ALL observed sales including stockout days (where is_stockout=1).
On stockout days, observed_sales = 0 or partial fill (NOT true demand).
Including these as demand=0 understates true demand and biases forecasts downward.

Tobit Model (Censored Regression):
- Stockout observations are LEFT-CENSORED: true demand >= observed_sales
- The Tobit model correctly handles this by treating stockout days as
  lower-bound observations rather than zero-demand observations

Simple Tobit Approximation:
1. Compute average demand on non-stockout days (clean observations)
2. For stockout days, impute demand using the clean average
   (scaled up slightly since stockouts correlate with high-demand days)
3. Recompute total demand forecast

Fix: Exclude or impute stockout observations using clean-day averages.
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/sales_inventory.csv")

# BUG: includes stockout days (is_stockout=1) as valid zero-demand observations
# This understates true demand
forecast_by_product = {}
for pid, group in df.groupby("sku_id"):
    # BUG: uses ALL days including stockout days in demand estimate
    avg_daily_demand = group["observed_sales"].mean()
    total_forecast = avg_daily_demand * 96
    forecast_by_product[pid] = round(float(total_forecast), 2)

total_forecast = sum(forecast_by_product.values())
n_stockout = df["is_stockout"].sum()

results = {
    "n_products": df["sku_id"].nunique(),
    "n_days": 96,
    "n_stockout_observations": int(n_stockout),
    "stockout_censoring_handled": False,   # BUG: should be True
    "tobit_applied": False,                # BUG: should be True
    "total_forecast_demand": round(float(total_forecast), 2),
    "forecast_by_product": forecast_by_product,
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Total forecast: {total_forecast:.2f} (WARNING: includes {n_stockout:.0f} stockout days as zero demand)")
print(f"Demand is UNDERSTATED — stockout observations bias mean downward")
