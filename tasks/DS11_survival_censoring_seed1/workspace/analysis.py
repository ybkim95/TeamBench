"""
Survival analysis script.
BUG: Computes naive median of ALL observed times, ignoring censoring status.
This UNDERESTIMATES true median survival because censored subjects have shorter
observed times than their true survival times.
Fix: Use Kaplan-Meier estimator (e.g., lifelines.KaplanMeierFitter) to correctly
account for censored observations.
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/survival_data.csv")

# BUG: naive median ignores censoring — computes median of ALL observed times
# including censored subjects who survived LONGER than their observed time.
naive_median = df["months_active"].median()

print(f"Naive median survival: {naive_median:.4f}")
print(f"WARNING: This is WRONG — it ignores censoring bias!")
print(f"Censoring rate: {1 - df['churned'].mean():.1%}")

results = {
    "median_survival": float(naive_median),
    "method": "naive_median",  # BUG: should be "kaplan_meier"
    "n_subjects": len(df),
    "event_rate": float(df["churned"].mean()),
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print("Saved results.json")
