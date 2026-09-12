# DS32: Cyclical Feature Encoding

## Task
Fix the feature encoding for **daily retail sales prediction by day of week** (1275 samples).
The `day_of_week` feature (period=7) must be encoded with sin/cos to preserve
the cyclic relationship.

## The Problem with Integer Encoding
Using `day_of_week` as a raw integer treats the transition from 6 to 0
as a jump of 6 units — but these time steps are adjacent!

With integer encoding:
- Distance(6, 0) = 6  ← WRONG: they are adjacent
- Distance(0, 1) = 1

With sin/cos encoding:
- Euclidean distance on unit circle between 6 and 0 ≈ 1.5637 ← small
- The cyclic structure is preserved

## Fix: Sin/Cos Transformation
```python
import numpy as np
df["sin_day_of_week"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
df["cos_day_of_week"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
```
Replace the integer `day_of_week` with `sin_day_of_week` and `cos_day_of_week` in the feature set.

## Data
File: `data/timeseries.csv`
- `day_of_week`: cyclic time feature (0 to 6)
- `sales_amount`: target variable
- Numeric features: `['store_size', 'promotions', 'foot_traffic']`

## Requirements
1. Add `sin_day_of_week` and `cos_day_of_week` columns using sin/cos encoding
2. Use `sin_day_of_week` and `cos_day_of_week` instead of raw integer `day_of_week`
3. Verify the cyclic distance between 6 and 0 is small (< 0.3)
4. Save to `results.json`:
   - `encoding_method`: `"sincos"`
   - `sin_col`: `"sin_day_of_week"`
   - `cos_col`: `"cos_day_of_week"`
   - `dist_period_minus1_to_0`: Euclidean distance on unit circle (≈ 1.5637, must be < 0.3)
   - `rmse`: model RMSE on full dataset
   - `n_samples`: 1275
   - `period_encoding`: dict with sin/cos values for period 5
     (sin≈-0.9749, cos≈-0.2225)
5. Fix `analysis.py`

## Deliverables
- Fixed `analysis.py` with sin/cos encoding
- `results.json` verifying cyclic property
