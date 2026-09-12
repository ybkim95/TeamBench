# Reference solution — GH1113_statsmodels_9747

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1113_statsmodels_9747`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1113_statsmodels_9747/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `statsmodels/emplike/descriptive.py` (modified, +9/-0)
- `statsmodels/emplike/tests/test_descriptive.py` (modified, +14/-0)

## Diff Summary (What the Fix Changes)

### `statsmodels/emplike/descriptive.py`
```diff
@@ -41,6 +41,15 @@ def DescStat(endog):
         If k=1, the function returns a univariate instance, DescStatUV.
         If k>1, the function returns a multivariate instance, DescStatMV.
     """
+    endog = np.asarray(endog)
+
+    if endog.size == 0:
+        raise ValueError("endog must contain data")
+    if endog.ndim == 0:
+        endog = endog.reshape(1,1)
+    if endog.ndim > 2:
+        raise ValueError("endog must be 1D or 2D")
+    
     if endog.ndim == 1:
         endog = endog.reshape(len(endog), 1)
     if endog.shape[1] == 1:
```

## Moved from `brief.md`

## Files That May Need Changes

- `statsmodels/emplike/descriptive.py`
