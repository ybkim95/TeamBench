# GH1063_FLAML_1419: Fix issue with "list index out of range" when max_iter=1 — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/microsoft/FLAML/issues/1416
- Repo: https://github.com/microsoft/FLAML

## Issue Description

### Describe the bug

Hi,  

I encountered an issue where setting `'mlflow_logging': True` along with `'max_iter': 1` results in a **'list index out of range'** error. However, when `'mlflow_logging': False` and `'max_iter': 1`, the code runs without any issues.

### Steps to reproduce

```python
from flaml import AutoML
import pandas as pd
import numpy as np
import mlflow

date_rng = pd.date_range(start='2024-01-01', periods=100, freq='H')
X = pd.DataFrame({'ds': date_rng})
y_train_24h = np.random.rand(len(X)) * 100  

settings = {
    "max_iter": 1,
    # "time_budget": 60,
    "estimator_list": ['xgboost'],
    "starting_points": {'xgboost': {}},
    "task": "ts_forecast",
    "log_file_name": "flaml_experiment.log",
    "seed": 41,
    "mlflow_exp_name": "Notebook1-AutoMLExperiment",
    "use_spark": False,
    "n_concurrent_trials": 3,
    "verbose": 1,
    "featurization": "off",
    "metric": "rmse",
    "mlflow_logging": True,
}

automl_24h = AutoML(**settings)

with mlflow.start_run(nested=True, run_name="AutoMLModel-XGBoost") as run:
    automl_24h.fit(
        X_train=X,
        y_train=y_train_24h,
        period=24,
        X_val=X,
        y_val=y_train_24h,
        split_ratio=0,
        force_cancel=False,
    )

best_model = automl_24h.model
print("Best model:", best_model)
print("Best run ID:", automl_24h.best_run_id)
```

### Screenshots and logs

![Image](https://github.com/user-attachments/assets/c8d26d96-2b2a-423c-bdb9-4c51706b3946)

### Additional Information

Python 3.11.9
FLAML Version 2.3.4

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Thank you [user] for raising the issue. Could you please provide more detailed reproduction steps and a traceback of the error?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
