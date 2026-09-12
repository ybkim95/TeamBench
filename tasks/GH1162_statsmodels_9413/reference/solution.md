# Reference solution — GH1162_statsmodels_9413

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1162_statsmodels_9413`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1162_statsmodels_9413/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `statsmodels/tsa/vector_ar/tests/test_var.py` (modified, +58/-57)
- `statsmodels/tsa/vector_ar/var_model.py` (modified, +40/-73)

## Diff Summary (What the Fix Changes)

### `statsmodels/tsa/vector_ar/var_model.py`
```diff
@@ -5,6 +5,7 @@
 ----------
 Lütkepohl (2005) New Introduction to Multiple Time Series Analysis
 """
+
 from __future__ import annotations
 
 from statsmodels.compat.python import lrange
@@ -226,12 +227,13 @@ def forecast(y, coefs, trend_coefs, steps, exog=None):
     -----
     Lütkepohl p. 37
     """
-    p = len(coefs)
-    k = len(coefs[0])
+    coefs = np.asarray(coefs)
+    if coefs.ndim != 3:
+        raise ValueError("coefs must be an array with 3 dimensions")
+    p, k = coefs.shape[:2]
     if y.shape[0] < p:
         raise ValueError(
-            f"y must by have at least order ({p}) observations. "
-            f"Got {y.shape[0]}."
+            f"y must by have at least order ({p}) observations. " f"Got {y.shape[0]}."
         )
     # initial value
     forcs = np.zeros((steps, k))
@@ -286,9 +288,7 @@ def _forecast_vars(steps, ma_coefs, sig_u):
     return covs[:, inds, inds]
 
 
-def forecast_interval(
-    y, coefs, trend_coefs, sig_u, steps=5, alpha=0.05, exog=1
-):
+def forecast_interval(y, coefs, trend_coefs, sig_u, steps=5, alpha=0.05, exog=1):
     assert 0 < alpha < 1
     q = util.norm_signif_level(alpha)
 
@@ -362,9 +362,7 @@ def _reordered(self, order):
             params_new_inc[0, i] = params[0, i]
             endog_lagged_new[:, 0] = endog_lagged[:, 0]
         for j in range(k_ar):
-            params_new_inc[i + j * num_end + k, :] = self.params[
-                c + j * num_end + k, :
-            ]
+            params_new_inc[i + j * num_end + k, :] = self.params[c + j * num_end + k, :]
             endog_lagged_new[:, i + j * num_end + k] = endog_lagged[
                 :, c + j * num_end + k
             ]
@@ -444,8 +442,8 @@ def test_normality(results, signif=0.05):
     Pinv = np.linalg.inv(np.linalg.cholesky(sig))
 
     w = np.dot(Pinv, resid_c.T)
-    b1 = (w ** 3).sum(1)[:, None] / results.nobs
-    b2 = (w ** 4).sum(1)[:, None] / results.nobs - 3
+    b1 = (w**3).sum(1)[:, None] / results.nobs
+    b2 = (w**4).sum(1)[:, N
```

## Moved from `brief.md`

## Files That May Need Changes

- `statsmodels/tsa/vector_ar/var_model.py`
