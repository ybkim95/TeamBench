# Reference solution — GH1100_darts_2984

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1100_darts_2984`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1100_darts_2984/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CHANGELOG.md` (modified, +2/-0)
- `darts/metrics/metrics.py` (modified, +12/-23)
- `darts/tests/metrics/test_metrics.py` (modified, +15/-5)

## Diff Summary (What the Fix Changes)

### `darts/metrics/metrics.py`
```diff
@@ -1744,8 +1744,8 @@ def sape(
     .. math::
         200 \\cdot \\frac{\\left| y_t - \\hat{y}_t \\right|}{\\left| y_t \\right| + \\left| \\hat{y}_t \\right|}
 
-    Note that it will raise a `ValueError` if :math:`\\left| y_t \\right| + \\left| \\hat{y}_t \\right| = 0` for some
-    :math:`t`. Consider using the Absolute Scaled Error (:func:`~darts.metrics.metrics.ase`)  in these cases.
+    When :math:`\\left| y_t \\right| + \\left| \\hat{y}_t \\right| = 0` for some :math:`t` (i.e., both actual and
+    prediction are zero), the error for that time step is defined as 0.
 
     If :math:`\\hat{y}_t` are stochastic (contains several samples) or quantile predictions, use parameter `q` to
     specify on which quantile(s) to compute the metric on. By default, it uses the median 0.5 quantile
@@ -1785,11 +1785,6 @@ def sape(
     verbose
         Optionally, whether to print operations progress.
 
-    Raises
-    ------
-    ValueError
-        If `actual_series` and `pred_series` contain some zeros at the same time index.
-
     Returns
     -------
     float
@@ -1822,14 +1817,14 @@ def sape(
         remove_nan_union=True,
         q=q,
     )
-    if not np.logical_or(y_true != 0, y_pred != 0).all():
-        raise_log(
-            ValueError(
-                "`actual_series` must be strictly positive to compute the sMAPE."
-            ),
-            logger=logger,
-        )
-    return 200.0 * np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred))
+    numerator = 200 * np.abs(y_true - y_pred)
+    denominator = np.abs(y_true) + np.abs(y_pred)
+    return np.divide(
+        numerator,
+        denominator,
+        out=np.zeros_like(numerator, dtype=y_true.dtype),
+        where=denominator != 0,
+    )
 
 
 @multi_ts_support
@@ -1854,9 +1849,8 @@ def smape(
         200 \\cdot \\frac{1}{T}
         \\sum_{t=1}^{T}{\\frac{\\left| y_t - \\hat{y}_t \\right|}{\\left| y_t \\right| + \\left| \\hat{y}_t \\right|} }
 
-    Note that it will raise a `ValueErr
```

## Moved from `brief.md`

## Files That May Need Changes

- `darts/metrics/metrics.py`
