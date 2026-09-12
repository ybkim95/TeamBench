"""
Funnel conversion analysis for trial signup to paid conversion funnel.
BUG: OLS regression on funnel-only sample WITHOUT Heckman selection correction.
Users who enter the funnel are self-selected — they have higher "product_fit_score" on
average. The OLS estimate of the feature effect on conversion is UPWARD-BIASED
because the selection process correlates with both the feature and the outcome.

Heckman Two-Step Correction:
1. Probit model: P(signed_up_trial=1 | product_fit_score) on FULL population
2. Compute Inverse Mills Ratio (IMR) = phi(xb) / Phi(xb) for each funnel member
3. OLS on funnel sample: converted_paid ~ product_fit_score + IMR
   The IMR controls for selection, giving unbiased coefficient on product_fit_score

Fix: implement Heckman two-step and include IMR as regressor.
"""
import pandas as pd
import numpy as np
import json
from scipy import stats

df = pd.read_csv("data/funnel_data.csv")

# BUG: OLS on funnel-only sample without selection correction
funnel = df[df["signed_up_trial"] == 1].copy()
funnel = funnel.dropna(subset=["converted_paid"])

x = funnel["product_fit_score"].values
y = funnel["converted_paid"].values.astype(float)

# BUG: simple OLS ignores selection bias
slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

results = {
    "n_population": len(df),
    "n_in_funnel": len(funnel),
    "feature_coefficient": round(float(slope), 4),
    "heckman_applied": False,         # BUG: should be True
    "imr_included": False,            # BUG: should be True
    "selection_bias_corrected": False, # BUG: should be True
    "r_squared": round(float(r_value**2), 4),
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Feature coefficient (biased OLS): {slope:.4f}")
print(f"WARNING: Selection bias not corrected — estimate is upward biased")
