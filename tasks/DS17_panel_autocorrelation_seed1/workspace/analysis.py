"""
Time-series regression for Fama-French 3-factor asset pricing.
BUG 1: Uses standard OLS standard errors, ignoring autocorrelation in residuals.
BUG 2: Does not compute Durbin-Watson statistic to detect autocorrelation.
BUG 3: Does not apply Newey-West HAC correction.

When residuals are autocorrelated, OLS SEs are TOO SMALL, inflating t-statistics.
Fix:
1. Compute Durbin-Watson statistic (DW < 2 indicates positive autocorrelation)
2. Apply Newey-West HAC standard errors with bandwidth = floor(4*(T/100)^(2/9))
   Use: result.get_robustcov_results(cov_type='HAC', use_correction=True, maxlags=4)
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/panel_data.csv").sort_values("month")

outcome = "excess_return"
predictors = ['market_return', 'smb_factor', 'hml_factor']
T = len(df)

X = np.column_stack([np.ones(T)] + [df[p].values for p in predictors])
y = df[outcome].values

# OLS
XtX_inv = np.linalg.inv(X.T @ X)
beta = XtX_inv @ X.T @ y
residuals = y - X @ beta

n, k = X.shape
sigma2 = np.sum(residuals**2) / (n - k)

# BUG: standard (homoscedastic, no-autocorrelation) SEs
se_ols = np.sqrt(np.diag(sigma2 * XtX_inv))

coef_names = ["intercept"] + predictors
results = {
    "coefficients": dict(zip(coef_names, [float(b) for b in beta])),
    "ols_se": dict(zip(coef_names, [float(s) for s in se_ols])),
    "nw_se": dict(zip(coef_names, [float(s) for s in se_ols])),  # BUG: same as OLS
    "dw_statistic": None,   # BUG: not computed
    "nw_bandwidth": None,   # BUG: not set
    "method": "ols",        # BUG: should be "newey_west"
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print("WARNING: OLS SEs not corrected for autocorrelation!")
print("Saved results.json")
