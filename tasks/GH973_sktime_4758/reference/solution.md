# Reference solution — GH973_sktime_4758

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH973_sktime_4758`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH973_sktime_4758/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `sktime/forecasting/dynamic_factor.py` (modified, +6/-12)
- `sktime/forecasting/tests/test_dynamic_factor.py` (added, +131/-0)

## Diff Summary (What the Fix Changes)

### `sktime/forecasting/dynamic_factor.py`
```diff
@@ -1,14 +1,13 @@
 # copyright: sktime developers, BSD-3-Clause License (see LICENSE file)
 """Implements DynamicFactor Model as interface to statsmodels."""
-
-import inspect
+from typing import List, Union
 
 import numpy as np
 import pandas as pd
 
 from sktime.forecasting.base.adapters import _StatsModelsAdapter
 
-_all_ = ["DynamicFactor"]
+__all__ = ["DynamicFactor"]
 __author__ = ["Ris-Bali", "lbventura"]
 
 
@@ -211,10 +210,8 @@ def _predict(self, fh, X=None):
         # beginning of the training series when passing integers
         start, end = fh.to_absolute_int(self._y.index[0], self.cutoff)[[0, -1]]
 
-        if "exog" in inspect.signature(self._forecaster.__init__).parameters.keys():
-            y_pred = self._fitted_forecaster.predict(start=start, end=end, exog=X)
-        else:
-            y_pred = self._fitted_forecaster.predict(start=start, end=end)
+        y_pred = self._fitted_forecaster.predict(start=start, end=end, exog=X)
+
         # statsmodels forecasts all periods from start to end of forecasting
         # horizon, but only return given time points in forecasting horizon
 
@@ -224,7 +221,7 @@ def _predict(self, fh, X=None):
             )
         return y_pred.loc[fh.to_absolute_index(self.cutoff)]
 
-    def _predict_interval(self, fh, X=None, coverage: [float] = None):
+    def _predict_interval(self, fh, X=None, coverage: Union[float, List[float]] = None):
         """Compute/return prediction quantiles for a forecast.
 
         private _predict_interval containing the core logic,
@@ -278,10 +275,7 @@ def _predict_interval(self, fh, X=None, coverage: [float] = None):
         for coverage in coverage_list:
             alpha = 1 - coverage
 
-            if "exog" in inspect.signature(model.__init__).parameters.keys():
-                y_pred = model.get_forecast(steps=steps, exog=X).conf_int(alpha=alpha)
-            else:
-                y_pred = model.get_forecast(steps=steps).conf_int(alpha=alpha)
+            y_pred = mode
```

## Moved from `brief.md`

## Files That May Need Changes

- `sktime/forecasting/dynamic_factor.py`
