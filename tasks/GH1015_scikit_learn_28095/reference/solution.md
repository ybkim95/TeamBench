# Reference solution — GH1015_scikit_learn_28095

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1015_scikit_learn_28095`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1015_scikit_learn_28095/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/whats_new/v1.4.rst` (modified, +1/-1)
- `sklearn/ensemble/_gb.py` (modified, +11/-4)
- `sklearn/ensemble/tests/test_gradient_boosting.py` (modified, +30/-2)

## Diff Summary (What the Fix Changes)

### `sklearn/ensemble/_gb.py`
```diff
@@ -65,16 +65,23 @@
 
 def _safe_divide(numerator, denominator):
     """Prevents overflow and division by zero."""
-    try:
+    # This is used for classifiers where the denominator might become zero exatly.
+    # For instance for log loss, HalfBinomialLoss, if proba=0 or proba=1 exactly, then
+    # denominator = hessian = 0, and we should set the node value in the line search to
+    # zero as there is no improvement of the loss possible.
+    # For numerical safety, we do this already for extremely tiny values.
+    if abs(denominator) < 1e-150:
+        return 0.0
+    else:
+        # Cast to Python float to trigger Python errors, e.g. ZeroDivisionError,
+        # without relying on `np.errstate` that is not supported by Pyodide.
+        result = float(numerator) / float(denominator)
         # Cast to Python float to trigger a ZeroDivisionError without relying
         # on `np.errstate` that is not supported by Pyodide.
         result = float(numerator) / float(denominator)
         if math.isinf(result):
             warnings.warn("overflow encountered in _safe_divide", RuntimeWarning)
         return result
-    except ZeroDivisionError:
-        warnings.warn("divide by zero encountered in _safe_divide", RuntimeWarning)
-        return 0.0
 
 
 def _init_raw_predictions(X, estimator, loss, use_predict_proba):
```

## Moved from `brief.md`

## Files That May Need Changes

- `sklearn/ensemble/_gb.py`
