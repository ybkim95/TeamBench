"""
Fairness audit for automated hiring screening model fairness audit.
BUG 1: Only computes selection rate — missing disparate impact ratio.
BUG 2: Missing demographic parity difference calculation.
BUG 3: Missing equalized odds (TPR/FPR per group).
BUG 4: No comparison to threshold — violations not identified.
Fix: Compute all required fairness metrics and flag violations.
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/predictions.csv")

protected_attr = "gender"
target = "shortlisted"
reference_group = "male"
di_threshold = 0.8

# BUG: Only computes selection rate — not disparate impact
selection_rates = df.groupby(protected_attr)[target].apply(lambda x: x.astype(float).mean())
print("Selection rates by group:")
print(selection_rates)

# BUG: No disparate impact calculation
# BUG: No demographic parity difference
# BUG: No equalized odds
# BUG: No violation flags

results = {}
for group in df[protected_attr].unique():
    rate = float(selection_rates[group])
    results[group] = {
        "selection_rate": rate,
        "disparate_impact": None,       # BUG: should be rate / ref_rate
        "demographic_parity_difference": None,  # BUG: should be rate - ref_rate
        "equalized_odds": None,         # BUG: should compute TPR/FPR
        "di_violation": None,           # BUG: should be disparate_impact < 0.8
    }

output = {
    "fairness_results": results,
    "reference_group": reference_group,
    "di_threshold": di_threshold,
    "violations_identified": [],        # BUG: should list groups below threshold
    "metrics_computed": ["selection_rate"],  # BUG: missing required metrics
}
with open("fairness_report.json", "w") as f:
    json.dump(output, f, indent=2)
print("Saved fairness_report.json")
