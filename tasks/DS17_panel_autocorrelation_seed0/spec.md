# DS17: Panel Autocorrelation — Newey-West Standard Errors

## Task
Fit an OLS regression for macroeconomic GDP growth regression (97 time periods) and produce
**correct inference** using Newey-West HAC standard errors.

## The Problem
Time-series residuals are **autocorrelated** (AR coefficient ≈ 0.45).
Standard OLS SEs understate true variability, inflating t-statistics.
The Durbin-Watson statistic will confirm positive autocorrelation (DW < 2).

## Requirements
1. Load `data/panel_data.csv`, sort by `quarter`
2. Fit OLS: regress `gdp_growth_pct` on `interest_rate`, `inflation_rate`, `unemployment_rate`
3. Compute **Durbin-Watson statistic** on residuals:
   ```python
   from statsmodels.stats.stattools import durbin_watson
   dw = durbin_watson(residuals)
   ```
4. Compute **Newey-West HAC standard errors** with bandwidth = 3:
   ```python
   import statsmodels.api as sm
   model = sm.OLS(y, X).fit()
   nw = model.get_robustcov_results(cov_type='HAC', use_correction=True, maxlags=3)
   ```
5. Save to `results.json`:
   - `coefficients`: dict of OLS estimates
   - `ols_se`: standard OLS standard errors
   - `nw_se`: Newey-West SE (should differ from OLS SEs)
   - `dw_statistic`: Durbin-Watson stat (expected in range [0.5, 1.8])
   - `nw_bandwidth`: 3 (use formula: `floor(4*(T/100)**(2/9))`)
   - `method`: `"newey_west"`
6. Fix `analysis.py`

## Bandwidth Formula
For T = 97: `bandwidth = floor(4 * (97/100)**(2/9)) = 3`

## Data
File: `data/panel_data.csv` — 97 observations

## Deliverables
- Fixed `analysis.py` with Newey-West HAC correction
- `results.json` with OLS SEs, NW SEs, DW stat, and bandwidth
