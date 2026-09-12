# Reference solution — GH907_autogluon_4272

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH907_autogluon_4272`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH907_autogluon_4272/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `tabular/src/autogluon/tabular/models/lgb/lgb_model.py` (modified, +4/-1)
- `tabular/tests/conftest.py` (modified, +4/-1)
- `tabular/tests/unittests/models/test_lightgbm.py` (modified, +19/-6)

## Diff Summary (What the Fix Changes)

### `tabular/src/autogluon/tabular/models/lgb/lgb_model.py`
```diff
@@ -252,10 +252,13 @@ def _fit(self, X, y, X_val=None, y_val=None, time_limit=None, num_gpus=0, num_cp
         else:
             self.params_trained["num_boost_round"] = self.model.current_iteration()
 
-    def _predict_proba(self, X, num_cpus=0, **kwargs):
+    def _predict_proba(self, X, num_cpus=0, **kwargs) -> np.ndarray:
         X = self.preprocess(X, **kwargs)
 
         y_pred_proba = self.model.predict(X, num_threads=num_cpus)
+        if self.problem_type == QUANTILE:
+            # y_pred_proba is a pd.DataFrame, need to convert
+            y_pred_proba = y_pred_proba.to_numpy()
         if self.problem_type in [REGRESSION, QUANTILE, MULTICLASS]:
             return y_pred_proba
         elif self.problem_type == BINARY:
```

## Moved from `brief.md`

## Files That May Need Changes

- `tabular/src/autogluon/tabular/models/lgb/lgb_model.py`
