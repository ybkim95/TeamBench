# DS15: Heteroscedasticity-Robust Inference (HC3)

## Task
Fit an OLS regression for house price regression with variance scaling with size (368 observations) and produce
**correct inference** using HC3 robust standard errors.

## The Problem
Standard OLS assumes homoscedastic errors (constant variance). This dataset has
**heteroscedastic** residuals — variance scales with `sqft`.
OLS standard errors are **too small**, inflating t-statistics and causing false positives.

## Requirements
1. Load `data/regression_data.csv`
2. Fit OLS: regress `log_price` on `sqft`, `age`, `bathrooms`, `distance_cbd`
3. Run **Breusch-Pagan test** for heteroscedasticity:
   - Use `statsmodels.stats.diagnostic.het_breuschpagan(residuals, X)`
   - Report test statistic and p-value
4. Compute **HC3 robust standard errors**:
   ```python
   import statsmodels.api as sm
   model = sm.OLS(y, X).fit()
   robust = model.get_robustcov_results(cov_type='HC3')
   ```
5. Save to `results.json`:
   - `coefficients`: dict of OLS estimates
   - `ols_se`: dict of standard OLS standard errors
   - `hc3_se`: dict of HC3 robust standard errors (should DIFFER from OLS SEs)
   - `bp_stat`: Breusch-Pagan test statistic (float)
   - `bp_pvalue`: Breusch-Pagan p-value (should be < 0.05 — reject homoscedasticity)
   - `method`: `"HC3"`
6. Fix `analysis.py`

## Key Check
The HC3 SEs for `age` should differ noticeably from OLS SEs.
The Breusch-Pagan test should REJECT the null of homoscedasticity (p < 0.05).

## Data
File: `data/regression_data.csv`

## Deliverables
- Fixed `analysis.py` with HC3 robust inference
- `results.json` with OLS SEs, HC3 SEs, and Breusch-Pagan test results
