"""
Data drift monitoring script for customer churn model monitoring.
BUG: Uses simple mean difference threshold instead of proper drift metrics.
Fix: Use PSI (Population Stability Index) or KS test for drift detection.
"""
import pandas as pd
import numpy as np
import json

ref = pd.read_csv("data/reference.csv")
prod = pd.read_csv("data/production.csv")

features = ['engagement_score', 'support_tickets_30d', 'tenure_months', 'monthly_spend', 'num_products']

drift_results = {}
for feat in features:
    ref_mean = ref[feat].astype(float).mean()
    prod_mean = prod[feat].astype(float).mean()

    # BUG: Uses relative mean difference — misses variance/distribution changes
    rel_diff = abs(prod_mean - ref_mean) / (ref_mean + 1e-8)

    # BUG: Arbitrary threshold on mean difference — not statistically grounded
    drifted = rel_diff > 0.15  # BUG: too simple, misses distribution shifts

    drift_results[feat] = {
        "ref_mean": float(ref_mean),
        "prod_mean": float(prod_mean),
        "relative_diff": float(rel_diff),
        "drifted": bool(drifted),
        "method": "mean_diff",  # BUG: should be PSI or KS
    }
    print(f"{feat}: rel_diff={rel_diff:.3f}, drifted={drifted}")

drifted_features = [f for f, r in drift_results.items() if r["drifted"]]
print(f"\nDrifted features: {drifted_features}")

output = {
    "drift_results": drift_results,
    "drifted_features": drifted_features,
    "psi_threshold": 0.2,
    "method": "mean_diff",  # BUG: should be PSI or KS
    "psi_computed": False,  # BUG: should be True
    "ks_test_applied": False,  # BUG: should be True
}
with open("drift_report.json", "w") as f:
    json.dump(output, f, indent=2)
print("Saved drift_report.json")
