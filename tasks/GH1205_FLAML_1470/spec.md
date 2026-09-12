# GH1205_FLAML_1470: Fix eval_set preprocessing for XGBoost estimators with categorical features — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/microsoft/FLAML

## PR Description

When using `flaml.default.XGBClassifier` or `XGBRegressor` with categorical features and an `eval_set` parameter, the validation data was not preprocessed, causing feature_names mismatch errors. FLAML's preprocessing reorders columns (categorical columns first), but this transformation was only applied to training data.

**Changes**

- **`flaml/default/estimator.py`**: Added eval_set preprocessing in the `fit` method
  - Transforms validation set features using `self._feature_transformer`
  - Transforms validation set labels using `self._label_transformer` when applicable (for rf, extra_tree, xgboost estimators)
  - Handles multiple eval_sets

- **`test/default/test_defaults.py`**: Extended `test_xgboost()` with categorical feature eval_set tests

**Example**

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from flaml.default import XGBClassifier

# Create data with categorical features
X = pd.DataFrame({
    "num1": [1, 2, 3, 4],
    "cat1": pd.Categorical(["A", "B", "A", "B"])
})
y = [0, 1, 0, 1]
X_train, X_valid, y_train, y_valid = train_test_split(X, y)

# Now works with eval_set
model = XGBClassifier(tree_method="hist", enable_categorical=True)
model.fit(X_train, y_train, eval_set=[(X_valid, y_valid)])
```

<!-- START COPILOT ORIGINAL PROMPT -->



<details>

<summary>Original prompt</summary>


----

*This section details on the original issue you should resolve*

<issue_title>[Bug]: flaml.default.XGBRegressor does not preprocess eval_set</issue_title>
<issue_description>### Describe the bug

Sometimes (when there are cat columns, for example) flaml (at least zero-shot) re-arranges columns. But for XGBRegressor/XGBClassifier, it misses to do that for the validation dataframe.

### Steps to reproduce

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score

# --- 1. Create synthetic dataset with numeric + categorical features ---
np.random.seed(42)
n = 1000

df = pd.DataFrame({
    "num1": np.random.randn(n),
    "num2": np.random.rand(n) * 10,
    "cat1": np.random.choice(["A", "B", "C"], size=n),
    "cat2": np.random.choice(["X", "Y"], size=n),
    "target": np.random.choice([0, 1], size=n)
})

# --- 2. Split data ---
X = df.drop(columns="target")
y = df["target"]

X_train, X_valid, y_train, y_valid = train_test_split(X, y, test_size=0.2, random_state=0)

# --- 3. Convert categorical columns to pandas 'category' dtype ---
for col in X_train.select_dtypes(include="object").columns:
    X_train[col] = X_train[col].astype("category")
    X_valid[col] = X_valid[col].astype("category")


# --- 4. Define XGBoost model ---
model = XGBClassifier(
    tree_method="hist",              # Efficient, supports categorical features
    enable_categorical=True,         # Important!
    eval_metric="logloss",
    use_label_encoder=False,
    early_stopping_rounds=10,
    random_state=0
)

# --- 5. Fit model with early stopping ---
model.fit(
    X_train, y_train,
    eval_set=[(X_valid, y_valid)],   # validation set for early stopping    
    verbose=True
)
```

> 
> [0]	validation_0-logloss:0.69096
> [1]	validation_0-logloss:0.69439
> [2]	validation_0-logloss:0.70184
> [3]	validation_0-logloss:0.70530
> [4]	validation_0-logloss:0.70542
> [5]	validation_0-logloss:0.70719
> [6]	validation_0-logloss:0.71508
> [7]	validation_0-logloss:0.71836
> [8]	validation_0-logloss:0.72136
> [9]	validation_0-logloss:0.72541

```python

import flaml.default as flaml_zeroshot

model = flaml_zeroshot.XGBClassifier(
    tree_method="hist",              # Efficient, supports categorical features
    enable_categorical=True,         # Important!
    eval_metric="logloss",
    use_label_encoder=False,
    early_stopping_rounds=10,
    random_state=0
)

# --- 5. Fit model with early stopping ---
model.fit(
    X_train, y_train,
    eval_set=[(X_valid, y_valid)],   # validation set for early stopping    
    verbose=True
)

```
> 
> ---------------------------------------------------------------------------
> ValueError                                Traceback (most recent call last)
> Cell In[4], line 13
>       3 model = flaml_zeroshot.XGBClassifier(
>       4     tree_method="hist",              # Efficient, supports categorical features
>       5     enable_categorical=True,         # Important!
>    (...)      9     random_state=0
>      10 )
>      12 # --- 5. Fit model with early stopping ---
> ---> 13 model.fit(
>      14     X_train, y_train,
>      15     eval_set=[(X_valid, y_valid)],   # validation set for early stopping    
>      16     verbose=True
>      17 )
> 
> File /venv/main/lib/python3.12/site-packages/flaml/default/estimator.py:106, in flamlize_estimator.<locals>.EstimatorClass.fit(self, X, y, *args, **params)
>      97 self.set_params(**hyperparams)
>      98 if self._label_transformer and estimator_name in [
>      99     "rf",
>     100     "extra_tree",
>    (...)    104 ]:
>     105     # rf and et have trouble in handling boolean labels; xgboost requires integer labels
> --> 106     fitted = super().fit(X, y_transformed, *args, **params)
>     107     # if hasattr(self, "_classes"):
>     108     #     self._classes = self._label_transformer.classes_
>     109     # else:
>     110     try:
> 
> File /venv/main/lib/python3.12/site-packages/xgboost/core.py:774, in require_keyword_args.<locals>.throw_if.<locals>.inner_f(*args, **kwargs)
>     772 for k, arg in zip(sig.parameters, args):
>     773     kwargs[k] = arg
> --> 774 return func(**kwargs)
> 
> File /venv/main/lib/python3.12/site-packages/xgboost/sklearn.py:1803, in XGBClassifier.fit(self, X, y, sample_weight, base_margin, eval_set, verbose, xgb_model, sample_weight_eval_set, base_margin_eval_set, feature_weights)
>    1783 evals_result: EvalsLog = {}
>    1784 train_dmatrix, evals = _wrap_evaluation_matrices(
>    1785     missing=self.missing,
>    1786     X=X,
>    (...)   1800     feature_types=feature_types,
>    1801 )
> -> 1803 self._Booster = train(
>    1804     params,
>    1805     train_dmatrix,
>    1806     self.get_num_boosting_rounds(),
>    1807     evals=evals,
>    1808     early_stopping_rounds=self.early_stopping_rounds,
>    1809     evals_result=evals_result,
>    1810     obj=obj,
>    1811     custom_m...

</details>



<!-- START COPILOT CODING AGENT SUFFIX -->

- Fixes microsoft/FLAML#1463

<!-- START COPILOT CODING AGENT TIPS -->
---

✨ Let Copilot coding agent [set things up for you](https://github.com/microsoft/FLAML/issues/new?title=✨+Set+up+Copilot+instructions&body=Configure%20instructions%20for%20this%20repository%20as%20documented%20in%20%5BBest%20practices%20for%20Copilot%20coding%20agent%20in%20your%20repository%5D%28https://gh.io/copilot-coding-agent-tips%29%2E%0A%0A%3COnboard%20this%20repo%3E&assignees=copilot) — coding agent works faster and does higher quality work when set up for your repo.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
