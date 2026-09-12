# DS39: Lag Feature Look-Ahead Bias

## Task
Fix look-ahead bias in lag feature computation for **electricity demand forecasting with lag features**
(568 time steps).

## The Bug
The buggy script uses `shift(-lag_val)` (negative shift) on the **full** dataset
before splitting. A negative shift looks **forward** in time:
- `df["lag_1"] = df["demand_mwh"].shift(-1)` assigns to row i the value from row i+1
- This means training features include future values from the test set
- The model at time t "sees" t+1 values — look-ahead bias

## Correct Approach: Positive Shift on Train Only
```python
df = df.sort_values("hour_idx").reset_index(drop=True)
# Split FIRST
train_raw = df.iloc[:455]
test_raw = df.iloc[455:]
# Then compute lags using POSITIVE shift (backward-looking)
for lag_name, lag_val in zip(['lag_1h', 'lag_2h', 'lag_3h', 'lag_24h'], [1, 2, 3, 24]):
    train_raw = train_raw.copy()
    train_raw[lag_name] = train_raw["demand_mwh"].shift(lag_val)  # past values only
train_raw = train_raw.dropna()
```

Key requirements:
1. Use `shift(+lag)` (positive = backward), not `shift(-lag)` (negative = forward)
2. Split train/test BEFORE computing lags
3. Drop NaN warmup rows from train

## Data
File: `data/timeseries.csv`
- `hour_idx`: time index (sort by this)
- `demand_mwh`: observed value
- `demand_next_hour`: next-step target

## Requirements
Save to `results.json`:
- `lag_method`: `"positive_shift_train_only"`
- `lag_names`: `['lag_1h', 'lag_2h', 'lag_3h', 'lag_24h']`
- `n_train`: number of training rows (after NaN drop)
- `n_test`: number of test rows
- `test_rmse`: test RMSE (should be HIGHER than leaky version — less optimistic)
- `lookahead_bias`: `false`
- `warmup_rows_dropped`: 24
- `temporal_order_verified`: `true`
Fix `analysis.py`.

## Deliverables
- Fixed `analysis.py` using `shift()` not `rolling(center=True)`
- `results.json` with correct lag features and honest test RMSE
