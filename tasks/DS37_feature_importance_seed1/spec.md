# DS37: Feature Importance Disagreement Resolution

## Task
Compute **multi-method feature importance** for **customer churn prediction feature importance analysis** (468 samples)
and identify features where methods disagree.

## The Problem with MDI
Mean Decrease in Impurity (MDI, `rf.feature_importances_`) is **biased**:
- High-cardinality features like `account_id_hash` get many tree splits
- MDI inflates their apparent importance even when they have no real signal
- True important features: `['tenure_months', 'monthly_charges']`

## Three Methods Required
1. **MDI** (impurity-based): `rf.feature_importances_`
2. **Permutation Importance** (unbiased):
   ```python
   from sklearn.inspection import permutation_importance
   perm = permutation_importance(rf, X, y, n_repeats=10, random_state=42)
   ```
3. **SHAP Approximation** (use TreeExplainer or linear approximation):
   ```python
   # Option A: sklearn SHAP-like via mean |coefficient| in linear model
   from sklearn.linear_model import LogisticRegression
   from sklearn.preprocessing import StandardScaler
   scaler = StandardScaler()
   lr = LogisticRegression(max_iter=500, random_state=42)
   lr.fit(scaler.fit_transform(X), y)
   shap_approx = np.abs(lr.coef_[0])
   ```

## Disagreement Detection
A feature shows **disagreement** if its rank differs by more than 2 between any two methods.

## Data
File: `data/dataset.csv`
- Target: `churned`
- Features: `['tenure_months', 'monthly_charges', 'contract_type', 'num_support_calls', 'payment_method_code', 'account_id_hash']`
- Note: `account_id_hash` has high cardinality but carries no signal

## Requirements
Save to `results.json`:
- `mdi_importances`: dict feature → MDI value
- `mdi_ranking`: features sorted by MDI (high to low)
- `permutation_importances`: dict feature → permutation importance mean
- `shap_importances`: dict feature → approximate SHAP magnitude
- `consensus_ranking`: list of features sorted by average rank across all 3 methods
- `disagreements`: list of features with rank difference > 2 between methods
- `method`: `"multi_method"`
- `n_samples`: 468
Fix `analysis.py`.

## Expected
`account_id_hash` should appear in `disagreements` (MDI ranks it high, permutation/SHAP rank it low).
`['tenure_months', 'monthly_charges']` should top the consensus ranking.

## Deliverables
- Fixed `analysis.py` with 3-method importance comparison
- `results.json` with consensus ranking and disagreements
