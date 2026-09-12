"""
Imputation script for employee_wellness dataset.

The dataset has 8 columns with missing values across 3 missingness types.
Current script applies global mean fill to ALL columns — this is wrong for:
  - MNAR columns: mean fill introduces systematic bias
  - MCAR-as-feature columns: mean fill destroys the meaningful absence signal

TASK: Apply the correct imputation strategy per column type (see spec).
NOTE: Not all columns need the same treatment.
      Mean fill is acceptable for MAR columns but wrong for MNAR and MCAR-feature columns.
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/dataset.csv")
print(f"Dataset shape: {df.shape}")
print(f"Missing value counts:")
print(df.isnull().sum())

all_cols = ['stress_self_report', 'manager_rating', 'overtime_hours_monthly', 'commute_time_minutes', 'last_salary_increase_pct', 'training_hours_ytd', 'performance_bonus_amount', 'external_offer_amount']
mcar_feature_cols = ['performance_bonus_amount', 'external_offer_amount']  # NOTE: these columns need special treatment per spec

# BUG: global mean fill for ALL columns
# - MNAR columns: mean fill introduces systematic bias
# - MCAR-feature columns: mean fill destroys the "absence = meaningful" signal
# - MAR columns: mean fill is OK but not ideal
for col in all_cols:
    if col in df.columns and col != "attrition_flag":
        mean_val = pd.to_numeric(df[col], errors="coerce").mean()
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(mean_val)
        print(f"Filled {col} with global mean: {mean_val:.2f}")

# BUG: no indicator columns created for MCAR-feature columns
# The absence of a value IS the signal for these columns

df.to_csv("data/imputed.csv", index=False)

# Compute imputation statistics for validation
stats = {}
for col in all_cols:
    if col in df.columns:
        stats[col] = {
            "mean": float(df[col].mean()),
            "median": float(df[col].median()),
            "std": float(df[col].std()),
        }

group_stats = {}
for col in ['stress_self_report', 'manager_rating', 'overtime_hours_monthly']:
    if col in df.columns:
        gs = df.groupby("seniority_band")[col].agg(["mean", "median", "count"])
        group_stats[col] = gs.to_dict()

stats["group_stats"] = group_stats

with open("imputation_stats.json", "w") as f:
    json.dump(stats, f, indent=2)
print("Saved data/imputed.csv and imputation_stats.json")
