"""
Categorical feature encoding for retail transaction value prediction.
BUG: Applies one-hot encoding to ALL categorical features regardless of cardinality.
High-cardinality features (e.g., store_id with 45 levels) create massive sparse
matrices that overfit, especially when categories are rare in test set.

Fix: Apply encoding strategy based on cardinality:
- Low cardinality (< 5 unique values): one-hot encoding (safe, interpretable)
- Medium cardinality (5-20 unique values): target encoding
- High cardinality (> 20 unique values): target encoding with smoothing (k=10)
"""
import pandas as pd
import numpy as np
import json

df = pd.read_csv("data/dataset.csv")
target_col = "purchase_amount"
cat_features = ['payment_type', 'product_category', 'store_id']
num_features = ['quantity', 'discount_pct', 'customer_age']

# BUG: one-hot encode ALL categoricals regardless of cardinality
X_parts = []
ohe_col_names = []
for col in cat_features:
    dummies = pd.get_dummies(df[col], prefix=col)
    X_parts.append(dummies.values)
    ohe_col_names.extend(dummies.columns.tolist())

X_num = df[num_features].values
X_parts.append(X_num)
X = np.hstack(X_parts)
y = df[target_col].values
n = len(y)

# Fit linear model
coef, _, _, _ = np.linalg.lstsq(
    np.column_stack([np.ones(n), X]), y, rcond=None
)
y_pred = np.column_stack([np.ones(n), X]) @ coef
ss_res = np.sum((y - y_pred)**2)
ss_tot = np.sum((y - y.mean())**2)
r2 = float(1 - ss_res / ss_tot)

results = {
    "encoding_strategy": {col: "one_hot" for col in cat_features},  # BUG: all OHE
    "n_features_after_encoding": X.shape[1],
    "encoding_method": "all_one_hot",  # BUG: should be "cardinality_aware"
    "r2": r2,
    "n_samples": n,
    "cardinalities": {col: int(df[col].nunique()) for col in cat_features},
    "low_card_threshold": None,  # BUG: not applied
    "high_card_threshold": None,  # BUG: not applied
}
with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"OHE all features: {X.shape[1]} total columns (expected ~59)")
print("WARNING: High-cardinality features OHE'd — likely overfitting!")
print("Saved results.json")
