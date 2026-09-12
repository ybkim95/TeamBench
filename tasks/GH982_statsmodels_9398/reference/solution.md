# Reference solution — GH982_statsmodels_9398

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH982_statsmodels_9398`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH982_statsmodels_9398/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `statsmodels/discrete/conditional_models.py` (modified, +7/-3)
- `statsmodels/discrete/tests/test_conditional.py` (modified, +78/-42)

## Diff Summary (What the Fix Changes)

### `statsmodels/discrete/conditional_models.py`
```diff
@@ -122,7 +122,12 @@ def fit(self,
             disp=disp,
             skip_hessian=skip_hessian)
 
-        crslt = ConditionalResults(self, rslt.params, rslt.cov_params(), 1)
+        if skip_hessian:
+            cov_params = None
+        else:
+            cov_params = rslt.cov_params()
+
+        crslt = ConditionalResults(self, rslt.params, cov_params, 1)
         crslt.method = method
         crslt.nobs = self.nobs
         crslt.n_groups = self._n_groups
@@ -232,8 +237,7 @@ class ConditionalLogit(_ConditionalModel):
 
     def __init__(self, endog, exog, missing='none', **kwargs):
 
-        super().__init__(
-            endog, exog, missing=missing, **kwargs)
+        super().__init__(endog, exog, missing=missing, **kwargs)
 
         if np.any(np.unique(self.endog) != np.r_[0, 1]):
             msg = "endog must be coded as 0, 1"
```

## Moved from `brief.md`

## Files That May Need Changes

- `statsmodels/discrete/conditional_models.py`
