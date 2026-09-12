# Reference solution — GH1096_autogluon_5131

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1096_autogluon_5131`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1096_autogluon_5131/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `timeseries/src/autogluon/timeseries/models/autogluon_tabular/mlforecast.py` (modified, +12/-2)
- `timeseries/tests/unittests/models/test_mlforecast.py` (modified, +21/-0)

## Diff Summary (What the Fix Changes)

### `timeseries/src/autogluon/timeseries/models/autogluon_tabular/mlforecast.py`
```diff
@@ -2,6 +2,7 @@
 import math
 import os
 import time
+import warnings
 from typing import Any, Callable, Collection, Dict, List, Optional, Tuple, Union
 
 import numpy as np
@@ -190,6 +191,11 @@ def _get_mlforecast_init_args(
             target_transforms.append(Differences(differences))
             self._sum_of_differences = sum(differences)
 
+        if "target_scaler" in model_params and "scaler" in model_params:
+            warnings.warn(
+                f"Both 'target_scaler' and 'scaler' hyperparameters are provided to {self.__class__.__name__}. "
+                "Please only set the 'target_scaler' parameter."
+            )
         # Support "scaler" for backward compatibility
         scaler_type = model_params.get("target_scaler", model_params.get("scaler"))
         if scaler_type is not None:
@@ -500,7 +506,9 @@ def is_quantile_model(self) -> bool:
 
     def get_hyperparameters(self) -> Dict[str, Any]:
         model_params = super().get_hyperparameters()
-        model_params.setdefault("target_scaler", "mean_abs")
+        # We don't set 'target_scaler' if user already provided 'scaler' to avoid overriding the user-provided value
+        if "scaler" not in model_params:
+            model_params.setdefault("target_scaler", "mean_abs")
         if "differences" not in model_params or model_params["differences"] is None:
             model_params["differences"] = []
         return model_params
@@ -660,7 +668,9 @@ class RecursiveTabularModel(AbstractMLForecastModel):
 
     def get_hyperparameters(self) -> Dict[str, Any]:
         model_params = super().get_hyperparameters()
-        model_params.setdefault("target_scaler", "standard")
+        # We don't set 'target_scaler' if user already provided 'scaler' to avoid overriding the user-provided value
+        if "scaler" not in model_params:
+            model_params.setdefault("target_scaler", "standard")
         if "differences" not in model_params or model_params["differences"] is None:
   
```

## Moved from `brief.md`

## Files That May Need Changes

- `timeseries/src/autogluon/timeseries/models/autogluon_tabular/mlforecast.py`
