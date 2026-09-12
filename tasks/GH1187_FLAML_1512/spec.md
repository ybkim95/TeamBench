# GH1187_FLAML_1512: Fix sklearn 1.7+ compatibility: BaseEstimator type detection for ensemble — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/microsoft/FLAML

## PR Description

sklearn 1.7+ changed estimator type detection from checking `_estimator_type` attribute to using `get_tags()`. Since `BaseEstimator` inherits from `ClassifierMixin`, FLAML regression estimators were incorrectly tagged as classifiers, causing `StackingRegressor` to reject them during ensemble construction.

## Changes

- **flaml/automl/model.py**: Override `__sklearn_tags__()` in `BaseEstimator` to dynamically return correct tags based on `_estimator_type` instance attribute set during initialization
- **test/automl/test_sklearn_17_compat.py**: Add compatibility tests for regression and classification estimators with sklearn's `is_regressor()`/`is_classifier()` checks

## Example

```python
from sklearn.base import is_regressor
from flaml.automl.model import ExtraTreesEstimator

# Before: returns False (incorrect)
# After: returns True (correct)
is_regressor(ExtraTreesEstimator(task='regression'))
```

The fix is backward compatible with sklearn < 1.7 where the old `_estimator_type` attribute mechanism still works.

<!-- START COPILOT ORIGINAL PROMPT -->



<details>

<summary>Original prompt</summary>

> 
> ----
> 
> *This section details on the original issue you should resolve*
> 
> <issue_title>[Bug]: Regression ensemble fails with scikit-learn 1.7.2: ValueError: The estimator ExtraTreesEstimator should be a regressor</issue_title>
> <issue_description>### Describe the bug
> 
> When running flaml.AutoML with task="regression" and ensemble=True, the AutoML search completes and then fails during the ensemble construction step (stacking). The failure happens inside scikit-learn StackingRegressor.fit() with:
> 
> ValueError: The estimator ExtraTreesEstimator should be a regressor.
> 
> This occurs even though the training matrix contains only numeric features (all float64, no object columns, no categorical dtype). I also see the warning:
> 
> Using passthrough=False for ensemble because the data contain categorical features.
> 
> …but the input data passed to fit() is purely numeric.
> 
> ### Steps to reproduce
> 
> ## Option A (minimal check, likely root cause)
> **Step 1: Install**
> ```bash
> pip install flaml==2.5.0 scikit-learn==1.7.2 numpy pandas lightgbm xgboost
> ````
> 
> **Step 2: Run**
> 
> ```python
> from sklearn.base import is_regressor
> from flaml.automl.model import ExtraTreesEstimator
> 
> print("is_regressor(ExtraTreesEstimator()):", is_regressor(ExtraTreesEstimator()))
> ```
> 
> **Step 3: Observe**
> The output is `False` (expected: `True`). This makes scikit-learn stacking validation fail when `ExtraTreesEstimator` is used as a base regressor.
> 
> ### Option B (end-to-end AutoML failure during ensemble building)
> 
> **Step 1: Install**
> 
> ```bash
> pip install flaml==2.5.0 scikit-learn==1.7.2 numpy pandas lightgbm xgboost catboost
> ```
> 
> **Step 2: Run**
> 
> ```python
> import numpy as np
> import pandas as pd
> from sklearn.model_selection import train_test_split
> from flaml import AutoML
> 
> # Numeric-only regression dataset
> rng = np.random.RandomState(42)
> X = pd.DataFrame(rng.randn(5000, 30), columns=[f"f{i}" for i in range(30)]).astype("float64")
> y = X["f0"] * 3.0 - X["f1"] * 2.0 + rng.randn(5000) * 0.1
> 
> print("dtypes (should be float64 only):")
> print(X.dtypes)
> 
> X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
> 
> automl = AutoML()
> automl.fit(
>     X_train=X_train,
>     y_train=y_train,
>     X_val=X_val,
>     y_val=y_val,
>     task="regression",
>     metric="rmse",
>     eval_method="holdout",
>     ensemble=True,
>     estimator_list=["extra_tree", "rf", "xgboost", "lgbm"],
>     time_budget=60,
>     verbose=3,
>     seed=42,
> )
> ```
> 
> **Step 3: Observe**
> The run crashes during ensemble building with:
> `ValueError: The estimator ExtraTreesEstimator should be a regressor.`
> 
> 
> 
> 
> ### Model Used
> 
> `flaml.AutoML` with `task="regression"`, `eval_method="holdout"`, `ensemble=True`, and a mixed estimator list including `extra_tree` (plus `rf`, `xgboost`, `lgbm`).
> 
> ### Expected Behavior
> 
> I expected FLAML to successfully build the ensemble model for regression, or (at minimum) skip any estimator that cannot be used as a regressor in stacking instead of raising a hard error.
> 
> ### Screenshots and logs
> 
> Relevant log lines and stack trace excerpt:
> 
> ```text
> [flaml.automl.logger: ...] INFO - Building ensemble with tuned estimators
> [flaml.automl.logger: ...] WARNING - Using passthrough=False for ensemble because the data contain categorical features.
> 
> ValueError: The estimator ExtraTreesEstimator should be a regressor.
>   ...
>   File .../sklearn/ensemble/_base.py:237, in _BaseHeterogeneousEnsemble._validate_estimators
>     raise ValueError("The estimator ExtraTreesEstimator should be a regressor.")
> ```
> 
> ### Additional Information
> 
> * FLAML Version: 2.5.0
> * scikit-learn Version: 1.7.2
> * Python Version: 3.10 (Conda env: `azureml_py310_sdkv2`)
> * Operating System: Linux (Azure ML Compute environment)
> * Data: numeric-only features (all `float64`, no categorical/object columns)</issue_description>
> 
> ## Comments on the Issue (you are [user] in this section)
> 
> <comments>
> </comments>
> 


</details>



<!-- START COPILOT CODING AGENT SUFFIX -->

- Fixes microsoft/FLAML#1511

<!-- START COPILOT CODING AGENT TIPS -->
---

💡 You can make Copilot smarter by setting up custom instructions, customizing its development environment and configuring Model Context Protocol (MCP) servers. Learn more [Copilot coding agent tips](https://gh.io/copilot-coding-agent-tips) in the docs.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
