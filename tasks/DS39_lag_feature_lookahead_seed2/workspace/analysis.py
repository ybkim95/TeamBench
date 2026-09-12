"""
Lag feature engineering for web traffic forecasting with lag features.
BUG: Lag features are computed BEFORE the train/test split using the full dataset.
The lags are then used in training — this causes look-ahead bias because when
computing lag_1 for row i, the script uses shift(-1) on the FULL dataset,
meaning training rows near the split boundary see future (test-set) values.

Fix:
1. Sort data by period_idx FIRST
2. Split train/test BEFORE computing lag features
3. Compute lag features using df['page_views'].shift(lag) on TRAIN only
4. For test set, concatenate train tail + test, shift, then slice test portion
5. Drop NaN warmup rows
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/timeseries.csv")
time_col = "period_idx"
value_col = "page_views"
target_col = "next_period_views"

# Step 1: sort by time (correct)
df = df.sort_values(time_col).reset_index(drop=True)

# BUG: compute lag features on full dataset using negative shift (looks ahead!)
for lag_name, lag_val in [('lag_1', 1), ('lag_2', 2), ('lag_7', 7), ('lag_14', 14)]:
    # BUG: shift(-lag_val) looks FORWARD into future observations
    df[lag_name] = df[value_col].shift(-lag_val)

# BUG: split after computing leaky features
n_train = 792
train = df.iloc[:n_train].dropna().copy()
test = df.iloc[n_train:].dropna().copy()

lag_names = [name for name, _ in [('lag_1', 1), ('lag_2', 2), ('lag_7', 7), ('lag_14', 14)]]
features = lag_names

X_train = train[features].values
y_train = train[target_col].values
X_test = test[features].values
y_test = test[target_col].values

# Fit model
from numpy.linalg import lstsq
X_tr_aug = np.column_stack([np.ones(len(X_train)), X_train])
coef, _, _, _ = lstsq(X_tr_aug, y_train, rcond=None)
X_te_aug = np.column_stack([np.ones(len(X_test)), X_test])
y_pred_test = X_te_aug @ coef
test_rmse = float(np.sqrt(np.mean((y_test - y_pred_test)**2)))

results = {
    "lag_method": "negative_shift_leaky",  # BUG: should be "positive_shift_train_only"
    "lag_names": lag_names,
    "n_train": len(train),
    "n_test": len(test),
    "test_rmse": test_rmse,
    "lookahead_bias": True,     # BUG marker
    "warmup_rows_dropped": 0,   # BUG: should drop max_lag rows
    "temporal_order_verified": True,
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Test RMSE (leaky rolling center): {test_rmse:.4f}")
print("WARNING: rolling(center=True) uses future values — look-ahead bias!")
print("Saved results.json")
