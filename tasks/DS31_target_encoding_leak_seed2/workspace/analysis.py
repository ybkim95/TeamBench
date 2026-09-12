"""
Feature engineering: target encoding for employee attrition prediction by department.
BUG: Target encoding is computed on the FULL dataset (train + test combined).
This leaks test-set target values into the encoded features, inflating
test performance metrics. This is a classic data leakage bug.

Fix: Split train/test FIRST, then compute target encoding statistics on
TRAIN set only. Apply (transform) the train encoding to the test set.
Add smoothing to handle rare/unseen categories.
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/dataset.csv")
target_col = "left_company"
cat_col = "department"
num_cols = ['salary', 'tenure_years', 'satisfaction_score']
n_train = 643

# BUG: Computing target encoding on the FULL dataset before splitting
# This leaks test target information into features!
global_mean = df[target_col].mean()
cat_means = df.groupby(cat_col)[target_col].mean()

# Apply leaky encoding to full dataset
df["cat_encoded"] = df[cat_col].map(cat_means).fillna(global_mean)

# Now split (too late — encoding already includes test targets)
train = df.iloc[:n_train].copy()
test = df.iloc[n_train:].copy()

features = num_cols + ["cat_encoded"]
X_train = train[features].values
y_train = train[target_col].values
X_test = test[features].values
y_test = test[target_col].values

# Simple correlation as proxy for model quality
from numpy.linalg import lstsq
coef, _, _, _ = lstsq(
    np.column_stack([np.ones(len(X_train)), X_train]),
    y_train, rcond=None
)
y_pred_test = np.column_stack([np.ones(len(X_test)), X_test]) @ coef

# BUG result: leaky encoding inflates test correlation
test_corr = float(np.corrcoef(y_pred_test, y_test)[0, 1])

results = {
    "global_mean": float(global_mean),
    "category_encodings": {k: float(v) for k, v in cat_means.items()},
    "encoding_method": "full_data",  # BUG: should be "train_only"
    "test_correlation": test_corr,
    "n_train": n_train,
    "n_test": len(test),
    "leakage_present": True,  # BUG marker
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"Test correlation (leaky): {test_corr:.4f}")
print("WARNING: Target encoding computed on full data — leakage present!")
print("Saved results.json")
