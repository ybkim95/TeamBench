# DS17: Panel Autocorrelation — Newey-West Standard Errors

## Task
Fit an OLS regression for climate temperature anomaly regression (120 time periods) and produce
**correct inference** using Newey-West HAC standard errors.

## The Problem
Time-series residuals are **autocorrelated** (AR coefficient ≈ 0.65).
Standard OLS SEs understate true variability, inflating t-statistics.
The Durbin-Watson statistic will confirm positive autocorrelation (DW < 2).

## Requirements
1. Load `data/panel_data.csv`, sort by `month_index`
2. Fit OLS: regress `temperature_anomaly` on `co2_ppm`, `solar_index`, `enso_index`
3. Compute **Durbin-Watson statistic** on residuals:
   ```python
   from statsmodels.stats.stattools import durbin_watson
   dw = durbin_watson(residuals)
   ```
4. Compute **Newey-West HAC standard errors** with bandwidth = 4:
   ```python
   import statsmodels.api as sm
   model = sm.OLS(y, X).fit()
   nw = model.get_robustcov_results(cov_type='HAC', use_correction=True, maxlags=4)
   ```
5. Save to `results.json`:
   - `coefficients`: dict of OLS estimates
   - `ols_se`: standard OLS standard errors
   - `nw_se`: Newey-West SE (should differ from OLS SEs)
   - `dw_statistic`: Durbin-Watson stat (expected in range [0.5, 1.8])
   - `nw_bandwidth`: 4 (use formula: `floor(4*(T/100)**(2/9))`)
   - `method`: `"newey_west"`
6. Fix `analysis.py`

## Bandwidth Formula
For T = 120: `bandwidth = floor(4 * (120/100)**(2/9)) = 4`

## Data
File: `data/panel_data.csv` — 120 observations

## Deliverables
- Fixed `analysis.py` with Newey-West HAC correction
- `results.json` with OLS SEs, NW SEs, DW stat, and bandwidth
