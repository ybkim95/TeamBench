"""
Churn analysis for streaming service subscriber churn analysis.
BUG: Treats upgraders as non-churners (event_type == "premium_upgrade" counted
as "active" in denominator). In reality, upgraders are RIGHT-CENSORED — they
leave the at-risk pool at upgrade time and should NOT be counted as non-churners.

This understates churn rate because upgraders inflate the denominator without
ever contributing a churn event. The population of upgraders is NOT a random
sample — they are typically more engaged (informative censoring), so their
removal changes the risk composition.

Fix: Exclude upgraders from both numerator and denominator.
Correct churn rate = n_churned / (n_total - n_upgraded)
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/subscriptions.csv")

n_total = len(df)
n_churned = df["churned"].sum()
n_upgraded = df["upgraded"].sum()

# BUG: treats upgraders as non-churners (includes them in denominator)
# churn_rate = churned / total (wrong: should exclude upgraders)
churn_rate = n_churned / n_total  # BUG: denominator includes upgraders

avg_tenure = df["observed_months"].mean()

results = {
    "n_total": int(n_total),
    "n_churned": int(n_churned),
    "n_upgraded": int(n_upgraded),
    "n_at_risk": int(n_total),     # BUG: should be n_total - n_upgraded
    "churn_rate": round(churn_rate, 4),
    "censoring_handled": False,    # BUG: should be True
    "avg_tenure_months": round(avg_tenure, 2),
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Churn rate: {churn_rate:.4f} (WARNING: upgraders treated as non-churners)")
print(f"Churned: {n_churned}, Upgraded: {n_upgraded}, Total: {n_total}")
