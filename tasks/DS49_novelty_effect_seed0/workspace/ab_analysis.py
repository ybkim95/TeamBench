"""
A/B test analysis for new UI feature A/B test with novelty effect.
BUG: Computes average treatment effect over the ENTIRE experiment period,
including early weeks with inflated novelty effect. This overstates the
true long-run (steady-state) effect of the treatment.

The novelty effect decays exponentially: users engage more with new features
initially, then settle into their true behavioral pattern.

Fix:
1. Fit exponential decay model to weekly_effect over time
2. Identify stabilization week: where effect stabilizes (< 10-20% above floor)
3. Report steady-state effect from post-stabilization weeks only
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/ab_test_weekly.csv")

# BUG: uses all weeks including novelty-inflated early weeks
control_col = "control_click_rate"
treatment_col = "treatment_click_rate"

# Average effect across all weeks (includes novelty period)
df["weekly_effect"] = df[treatment_col] - df[control_col]
naive_ate = df["weekly_effect"].mean()

# BUG: no decay detection or stabilization analysis
results = {
    "n_weeks_used": len(df),           # BUG: should use only post-decay weeks
    "stabilization_week": 1,           # BUG: should detect actual stabilization
    "novelty_corrected": False,         # BUG: should be True
    "treatment_effect": round(float(naive_ate), 4),
    "avg_control_click_rate": round(float(df[control_col].mean()), 4),
    "avg_treatment_click_rate": round(float(df[treatment_col].mean()), 4),
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Treatment effect (all weeks): {naive_ate:.4f}")
print(f"WARNING: Includes novelty-inflated early weeks — effect is overstated")
