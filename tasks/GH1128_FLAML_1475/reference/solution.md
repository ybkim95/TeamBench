# Reference solution — GH1128_FLAML_1475

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1128_FLAML_1475`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1128_FLAML_1475/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `flaml/automl/automl.py` (modified, +123/-6)
- `test/automl/test_multiclass.py` (modified, +26/-0)
- `website/docs/FAQ.md` (modified, +77/-6)
- `website/docs/Use-Cases/Task-Oriented-AutoML.md` (modified, +55/-0)

## Diff Summary (What the Fix Changes)

### `flaml/automl/automl.py`
```diff
@@ -503,18 +503,135 @@ def best_iteration(self):
 
     @property
     def best_config(self):
-        """A dictionary of the best configuration."""
+        """A dictionary of the best configuration.
+
+        The returned config dictionary can be used to:
+        1. Pass as `starting_points` to a new AutoML run.
+        2. Initialize the corresponding FLAML estimator directly.
+        3. Initialize the original model (e.g., LightGBM, XGBoost) after converting
+           FLAML-specific parameters.
+
+        Note:
+            The config contains FLAML's search space parameters, which may differ from
+            the original model's parameters. For example, FLAML uses `log_max_bin` for
+            LightGBM instead of `max_bin`. Use the FLAML estimator's `config2params()`
+            method to convert to the original model's parameters.
+
+        Example:
+
+        ```python
+        from flaml import AutoML
+        from flaml.automl.model import LGBMEstimator
+        from lightgbm import LGBMClassifier
+        from sklearn.datasets import load_iris
+
+        X, y = load_iris(return_X_y=True)
+
+        # Train with AutoML
+        automl = AutoML()
+        automl.fit(X, y, task="classification", time_budget=10)
+
+        # Get the best config
+        best_config = automl.best_config
+        print("Best config:", best_config)
+        # Example output: {'n_estimators': 4, 'num_leaves': 4, 'min_child_samples': 20,
+        #                  'learning_rate': 0.1, 'log_max_bin': 8, ...}
+
+        # Option 1: Use FLAML estimator directly (handles parameter conversion internally)
+        flaml_estimator = LGBMEstimator(task="classification", **best_config)
+        flaml_estimator.fit(X, y)
+
+        # Option 2: Convert to original model parameters using config2params()
+        # This converts FLAML-specific params (e.g., log_max_bin -> max_bin)
+        original_params = flaml_estimator.params  # or use flaml_estimator.config2params(best_config)
+
```

## Moved from `brief.md`

## Files That May Need Changes

- `flaml/automl/automl.py`
