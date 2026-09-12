# DS45: Forecast Structural Break Detection (Chow Test)

## Task
Forecast the next period of `monthly_revenue` from a **48-period** time series
with a **structural break** (regime change) at some unknown period.

## The Problem
The time series has two distinct regimes:
- **Pre-break**: slower trend (slope ≈ 0.561)
- **Post-break**: faster trend (slope ≈ 7.827)

A single OLS model blends both regimes, producing biased forecasts.

## Chow Test for Break Detection
To find the structural break:
1. For each candidate breakpoint `k` from 5 to n-5:
   - Fit OLS on periods [1..k] → compute RSS_pre
   - Fit OLS on periods [k+1..n] → compute RSS_post
   - Record RSS_pre + RSS_post
2. The breakpoint with **minimum combined RSS** is the detected break
3. Alternatively compute Chow F-statistic at each candidate

## Data
File: `data/time_series.csv`
- `period`: integer time period (1 to 48)
- `monthly_revenue`: observed value

## Requirements
1. Load `data/time_series.csv`
2. Detect structural break using minimum combined RSS across candidate breakpoints
3. Fit OLS model on post-break segment only
4. Forecast period `49` using post-break model
5. Save to `results.json`:
   - `model`: `"piecewise_ols"`
   - `break_detected`: `true`
   - `break_point`: detected breakpoint period
   - `forecast_next_period`: next-period forecast
   - `rmse`: RMSE of post-break model fit
6. Fix `forecast.py`

## Expected Results
- True break at period 29
- Correct forecast ≈ 469.04
- Buggy (single trend) forecast ≈ 416.99

## Deliverables
- Fixed `forecast.py`
- `results.json` with piecewise OLS forecast
