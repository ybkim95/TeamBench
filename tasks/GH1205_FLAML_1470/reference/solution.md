# Reference solution — GH1205_FLAML_1470

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1205_FLAML_1470`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1205_FLAML_1470/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `flaml/default/estimator.py` (modified, +21/-0)
- `test/default/test_defaults.py` (modified, +61/-0)

## Diff Summary (What the Fix Changes)

### `flaml/default/estimator.py`
```diff
@@ -95,6 +95,27 @@ def suggest_hyperparams(self, X, y):
         def fit(self, X, y, *args, **params):
             hyperparams, estimator_name, X, y_transformed = self.suggest_hyperparams(X, y)
             self.set_params(**hyperparams)
+
+            # Transform eval_set if present
+            if "eval_set" in params and params["eval_set"] is not None:
+                transformed_eval_set = []
+                for eval_X, eval_y in params["eval_set"]:
+                    # Transform features
+                    eval_X_transformed = self._feature_transformer.transform(eval_X)
+                    # Transform labels if applicable
+                    if self._label_transformer and estimator_name in [
+                        "rf",
+                        "extra_tree",
+                        "xgboost",
+                        "xgb_limitdepth",
+                        "choose_xgb",
+                    ]:
+                        eval_y_transformed = self._label_transformer.transform(eval_y)
+                        transformed_eval_set.append((eval_X_transformed, eval_y_transformed))
+                    else:
+                        transformed_eval_set.append((eval_X_transformed, eval_y))
+                params["eval_set"] = transformed_eval_set
+
             if self._label_transformer and estimator_name in [
                 "rf",
                 "extra_tree",
```

## Moved from `brief.md`

## Files That May Need Changes

- `flaml/default/estimator.py`
