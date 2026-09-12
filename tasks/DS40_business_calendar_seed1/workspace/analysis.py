"""
Date feature engineering for tech ad revenue with fiscal year starting Oct (Q1=Oct-Dec).
BUG: Uses only standard calendar features (year, month, day_of_week).
Missing business-calendar features:
1. Fiscal quarter differs from calendar quarter (fiscal year starts month 10)
2. Company holidays not flagged (these drive demand spikes)
3. No "days to fiscal quarter end" feature (important for financial targets)
4. High-season flag not computed

Fix: add fiscal_quarter, is_company_holiday, days_to_fiscal_quarter_end,
and is_high_season features.
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/daily_data.csv")
target_col = "ad_revenue"

# BUG: Only standard calendar features — no business calendar context
# Missing: fiscal_quarter, company holidays, quarter-end proximity, high season
df["calendar_quarter"] = ((df["month"] - 1) // 3 + 1)  # BUG: wrong for fiscal

# BUG: no company holiday flag
# BUG: no days-to-fiscal-quarter-end
# BUG: no high-season flag

features = ["year", "month", "day_of_week", "calendar_quarter"]
X = df[features].values
y = df[target_col].values
n = len(y)

from numpy.linalg import lstsq
coef, _, _, _ = lstsq(np.column_stack([np.ones(n), X]), y, rcond=None)
y_pred = np.column_stack([np.ones(n), X]) @ coef
rmse = float(np.sqrt(np.mean((y - y_pred)**2)))

results = {
    "features_used": features,
    "fiscal_quarter_computed": False,   # BUG
    "is_company_holiday_computed": False,  # BUG
    "days_to_fiscal_quarter_end_computed": False,  # BUG
    "is_high_season_computed": False,   # BUG
    "rmse": rmse,
    "n_samples": n,
    "fiscal_year_start_month": None,    # BUG: not set
    "n_holidays_flagged": 0,            # BUG
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Calendar features only RMSE: {rmse:.4f}")
print("WARNING: Missing fiscal quarter, company holidays, and high-season flag!")
print("Saved results.json")
