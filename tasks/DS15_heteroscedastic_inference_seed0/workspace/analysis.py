"""
OLS regression for wage regression with heteroscedastic residuals.
BUG: Uses standard (non-robust) OLS standard errors.
When residual variance is heteroscedastic (varies with predictors), OLS SEs are
biased — usually TOO SMALL — inflating t-statistics and creating false positives.
Fix: Use HC3 heteroscedasticity-consistent standard errors (White's sandwich estimator).
Use statsmodels: result.get_robustcov_results(cov_type='HC3')
Also run Breusch-Pagan test to confirm heteroscedasticity.
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/regression_data.csv")
outcome = "log_wage"
predictors = ['education', 'experience', 'tenure', 'union_member']

X = np.column_stack([np.ones(len(df))] + [df[p].values for p in predictors])
y = df[outcome].values

# OLS via normal equations
XtX_inv = np.linalg.inv(X.T @ X)
beta = XtX_inv @ X.T @ y
residuals = y - X @ beta

n, k = X.shape
sigma2 = np.sum(residuals**2) / (n - k)

# BUG: homoscedastic (OLS) standard errors
se_ols = np.sqrt(np.diag(sigma2 * XtX_inv))

t_stats = beta / se_ols
p_values = [2 * (1 - abs(t) / (abs(t) + n - k)**0.5) for t in t_stats]  # approx

coef_names = ["intercept"] + predictors
results = {
    "coefficients": dict(zip(coef_names, [float(b) for b in beta])),
    "ols_se": dict(zip(coef_names, [float(s) for s in se_ols])),
    "hc3_se": dict(zip(coef_names, [float(s) for s in se_ols])),  # BUG: same as OLS
    "bp_stat": None,       # BUG: not computed
    "bp_pvalue": None,     # BUG: not computed
    "method": "ols",       # BUG: should detect and correct for heteroscedasticity
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print("OLS coefficients:", dict(zip(coef_names, [round(b,4) for b in beta])))
print("WARNING: OLS SEs not robust to heteroscedasticity!")
print("Saved results.json")
