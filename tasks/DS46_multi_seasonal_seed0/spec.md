# DS46: Seasonality Decomposition with Multiple Periods (MSTL)

## Task
Decompose a **278-day** `daily_sales` time series for daily retail sales with weekly and monthly seasonality
with **two seasonal components**: weekly (period=7) and monthly (period=30).

## The Problem
Single-period STL only removes one seasonal component. With multiple seasonal patterns,
the residuals contain the un-modeled seasonality, making them non-white-noise.

- **Buggy**: STL with weekly period only → residual ACF at lag 30 ≈ 0.836 (high)
- **Correct**: MSTL removing both → residual ACF at lag 30 ≈ 0.011 (near zero)

## MSTL Algorithm
```
deseasonalized = y.copy()
seasonal = {}
for period in [weekly_period, monthly_period]:
    # Apply simple STL approximation:
    # Trend: moving average with window = period
    # Seasonal: mean deviation from trend, repeated
    trend = moving_average(deseasonalized, window=period)
    raw_seasonal = deseasonalized - trend
    # Average seasonal pattern for this period
    s = np.zeros(len(y))
    for i in range(len(y)):
        same_phase = [raw_seasonal[j] for j in range(len(y)) if j % period == i % period]
        s[i] = np.mean(same_phase)
    seasonal[period] = s
    deseasonalized = deseasonalized - s
trend_final = moving_average(deseasonalized, window=monthly_period)
residuals = y - trend_final - sum(seasonal.values())
```

## Data
File: `data/daily_series.csv`
- `day`: integer day index (1 to 278)
- `daily_sales`: observed daily value

## Requirements
1. Load `data/daily_series.csv`
2. Apply MSTL with periods 7 and 30
3. Save to `results.json`:
   - `periods_used`: `[7, 30]`
   - `mstl_applied`: `true`
   - `monthly_component_extracted`: `true`
   - `residual_acf_lag30`: ACF of residuals at lag 30 (should be < 0.15)
   - `seasonal_weekly_amplitude`: std of weekly component
   - `seasonal_monthly_amplitude`: std of monthly component (should be > 0)
4. Fix `decompose.py`

## Deliverables
- Fixed `decompose.py`
- `results.json` with MSTL decomposition
