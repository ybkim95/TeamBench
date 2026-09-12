# DS32: Cyclical Feature Encoding

## Task
Fix the feature encoding for **hourly energy consumption prediction** (2729 samples).
The `hour` feature (period=24) must be encoded with sin/cos to preserve
the cyclic relationship.

## The Problem with Integer Encoding
Using `hour` as a raw integer treats the transition from 23 to 0
as a jump of 23 units — but these time steps are adjacent!

With integer encoding:
- Distance(23, 0) = 23  ← WRONG: they are adjacent
- Distance(0, 1) = 1

With sin/cos encoding:
- Euclidean distance on unit circle between 23 and 0 ≈ 0.2611 ← small
- The cyclic structure is preserved

## Fix: Sin/Cos Transformation
```python
import numpy as np
df["sin_hour"] = np.sin(2 * np.pi * df["hour"] / 24)
df["cos_hour"] = np.cos(2 * np.pi * df["hour"] / 24)
```
Replace the integer `hour` with `sin_hour` and `cos_hour` in the feature set.

## Data
File: `data/timeseries.csv`
- `hour`: cyclic time feature (0 to 23)
- `kwh_demand`: target variable
- Numeric features: `['temperature', 'humidity', 'is_weekend']`

## Requirements
1. Add `sin_hour` and `cos_hour` columns using sin/cos encoding
2. Use `sin_hour` and `cos_hour` instead of raw integer `hour`
3. Verify the cyclic distance between 23 and 0 is small (< 0.3)
4. Save to `results.json`:
   - `encoding_method`: `"sincos"`
   - `sin_col`: `"sin_hour"`
   - `cos_col`: `"cos_hour"`
   - `dist_period_minus1_to_0`: Euclidean distance on unit circle (≈ 0.2611, must be < 0.3)
   - `rmse`: model RMSE on full dataset
   - `n_samples`: 2729
   - `period_encoding`: dict with sin/cos values for period 8
     (sin≈0.8660, cos≈-0.5000)
5. Fix `analysis.py`

## Deliverables
- Fixed `analysis.py` with sin/cos encoding
- `results.json` verifying cyclic property
