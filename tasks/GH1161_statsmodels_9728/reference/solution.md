# Reference solution — GH1161_statsmodels_9728

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1161_statsmodels_9728`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1161_statsmodels_9728/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/source/conf.py` (modified, +1/-1)
- `examples/notebooks/ordinal_regression.ipynb` (modified, +1/-1)
- `examples/python/ordinal_regression.py` (modified, +1/-1)
- `statsmodels/compat/matplotlib.py` (added, +11/-0)
- `statsmodels/graphics/gofplots.py` (modified, +2/-2)
- `statsmodels/graphics/tests/test_tsaplots.py` (modified, +66/-17)
- `statsmodels/graphics/tsaplots.py` (modified, +36/-40)
- `statsmodels/nonparametric/_smoothers_lowess.pyx` (modified, +1/-1)
- `statsmodels/nonparametric/smoothers_lowess.py` (modified, +1/-1)
- `statsmodels/nonparametric/smoothers_lowess_old.py` (modified, +1/-1)

## Diff Summary (What the Fix Changes)

### `docs/source/conf.py`
```diff
@@ -429,7 +429,7 @@
 import statsmodels.tsa.api as tsa
 import statsmodels.formula.api as smf
 import numpy as np
-import scipy.stats as stats
+from scipy import stats
 import matplotlib.pyplot as plt
 import pandas as pd
 """
```

### `examples/python/ordinal_regression.py`
```diff
@@ -11,7 +11,7 @@
 
 import numpy as np
 import pandas as pd
-import scipy.stats as stats
+from scipy import stats
 
 from statsmodels.miscmodels.ordinal_model import OrderedModel
 
```

### `statsmodels/compat/matplotlib.py`
```diff
@@ -0,0 +1,11 @@
+from packaging.version import Version, parse
+
+try:
+    import matplotlib as mpl
+
+    version = parse(mpl.__version__)
+    MPL_LT_310 = version < Version("3.9.99")
+except ImportError:
+    MPL_LT_310 = False
+
+__all__ = ["MPL_LT_310"]
```

### `statsmodels/graphics/gofplots.py`
```diff
@@ -94,7 +94,7 @@ class ProbPlot:
     degrees of freedom:
 
     >>> # example 2
-    >>> import scipy.stats as stats
+    >>> from scipy import stats
     >>> pplot = sm.ProbPlot(res, stats.t, distargs=(4,))
     >>> fig = pplot.qqplot()
     >>> h = plt.title("Ex. 2 - qqplot - residuals against quantiles of t-dist")
@@ -658,7 +658,7 @@ def qqplot(
     qqplot of the residuals against quantiles of t-distribution with 4 degrees
     of freedom:
 
-    >>> import scipy.stats as stats
+    >>> from scipy import stats
     >>> fig = sm.qqplot(res, stats.t, distargs=(4,))
     >>> plt.show()
 
```

### `statsmodels/graphics/tsaplots.py`
```diff
@@ -1,4 +1,5 @@
 """Correlation plot functions."""
+
 from statsmodels.compat.pandas import deprecate_kwarg
 
 import calendar
@@ -79,9 +80,7 @@ def _plot_corr(
         lags = lags.astype(float)
         lags[np.argmin(lags)] -= 0.5
         lags[np.argmax(lags)] += 0.5
-        ax.fill_between(
-            lags, confint[:, 0] - acf_x, confint[:, 1] - acf_x, alpha=0.25
-        )
+        ax.fill_between(lags, confint[:, 0] - acf_x, confint[:, 1] - acf_x, alpha=0.25)
 
 
 @deprecate_kwarg("unbiased", "adjusted")
@@ -378,20 +377,20 @@ def plot_pacf(
 
 
 def plot_ccf(
-        x,
-        y,
-        *,
-        ax=None,
-        lags=None,
-        negative_lags=False,
-        alpha=0.05,
-        use_vlines=True,
-        adjusted=False,
-        fft=False,
-        title="Cross-correlation",
-        auto_ylims=False,
-        vlines_kwargs=None,
-        **kwargs,
+    x,
+    y,
+    *,
+    ax=None,
+    lags=None,
+    negative_lags=False,
+    alpha=0.05,
+    use_vlines=True,
+    adjusted=False,
+    fft=False,
+    title="Cross-correlation",
+    auto_ylims=False,
+    vlines_kwargs=None,
+    **kwargs,
 ):
     """
     Plot the cross-correlation function
@@ -466,9 +465,7 @@ def plot_ccf(
     if negative_lags:
         lags = -lags
 
-    ccf_res = ccf(
-        x, y, adjusted=adjusted, fft=fft, alpha=alpha, nlags=nlags + 1
-    )
+    ccf_res = ccf(x, y, adjusted=adjusted, fft=fft, alpha=alpha, nlags=nlags + 1)
     if alpha is not None:
         ccf_xy, confint = ccf_res
     else:
@@ -493,22 +490,22 @@ def plot_ccf(
 
 
 def plot_accf_grid(
-        x,
-        *,
-        varnames=None,
-        fig=None,
-        lags=None,
-        negative_lags=True,
-        alpha=0.05,
-        use_vlines=True,
-        adjusted=False,
-        fft=False,
-        missing="none",
-        zero=True,
-        auto_ylims=False,
-        bartlett_confint=False,
-        vlines_kwargs=None,
-        **kwargs,
+    x,
+    *,
+    varnames=None,
+    fig=None,
+  
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `docs/source/conf.py`
- `examples/python/ordinal_regression.py`
- `statsmodels/compat/matplotlib.py`
- `statsmodels/graphics/gofplots.py`
- `statsmodels/graphics/tsaplots.py`
