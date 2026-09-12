"""
Revenue forecast after price change for retail product pricing analysis.
BUG: Assumes demand stays CONSTANT after price change — ignores price elasticity.
Revenue is computed as old_demand * new_price, which overstates revenue when
price increases (demand decreases) and understates when price decreases.

Price elasticity of demand formula:
  new_demand = old_demand * (new_price / old_price) ^ elasticity
  revenue = new_demand * new_price

For elastic demand (elasticity < -1): a price increase DECREASES revenue.
For inelastic demand (-1 < elasticity < 0): a price increase INCREASES revenue.

Fix: use the elasticity column to compute demand response before forecasting revenue.
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/product_pricing.csv")

# BUG: ignores elasticity — assumes demand stays constant
df["new_demand"] = df["old_demand"]  # BUG: demand does NOT change with price
df["forecast_revenue"] = df["new_demand"] * df["new_price"]  # BUG: overstated

total_old_revenue = (df["old_demand"] * df["old_price"]).sum()
total_new_revenue = df["forecast_revenue"].sum()
revenue_change_pct = (total_new_revenue - total_old_revenue) / total_old_revenue

results = {
    "n_products": len(df),
    "price_change_pct": 0.21,
    "elasticity_applied": False,       # BUG: should be True
    "total_old_revenue": round(float(total_old_revenue), 2),
    "total_forecast_revenue": round(float(total_new_revenue), 2),
    "revenue_change_pct": round(float(revenue_change_pct), 4),
    "avg_demand_change_pct": 0.0,      # BUG: should reflect elasticity-driven change
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Forecast revenue: {total_new_revenue:.2f} (WARNING: ignores demand elasticity)")
print(f"Revenue change: {revenue_change_pct:.1%}")
