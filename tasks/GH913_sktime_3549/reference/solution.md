# Reference solution — GH913_sktime_3549

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH913_sktime_3549`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH913_sktime_3549/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `sktime/forecasting/compose/_pipeline.py` (modified, +2/-4)
- `sktime/forecasting/compose/tests/test_pipeline.py` (modified, +28/-0)

## Diff Summary (What the Fix Changes)

### `sktime/forecasting/compose/_pipeline.py`
```diff
@@ -299,7 +299,7 @@ class ForecastingPipeline(_Pipeline):
         "X_inner_mtype": SUPPORTED_MTYPES,
         "ignores-exogeneous-X": False,
         "requires-fh-in-fit": False,
-        "handles-missing-data": False,
+        "handles-missing-data": True,
         "capability:pred_int": True,
         "X-y-must-have-same-index": False,
     }
@@ -311,7 +311,6 @@ def __init__(self, steps):
         tags_to_clone = [
             "ignores-exogeneous-X",  # does estimator ignore the exogeneous X?
             "capability:pred_int",  # can the estimator produce prediction intervals?
-            "handles-missing-data",  # can estimator handle missing data?
             "requires-fh-in-fit",  # is forecasting horizon already required in fit?
             "enforce_index_type",  # index type that needs to be enforced in X/y
         ]
@@ -713,7 +712,7 @@ class TransformedTargetForecaster(_Pipeline):
         "X_inner_mtype": SUPPORTED_MTYPES,
         "ignores-exogeneous-X": False,
         "requires-fh-in-fit": False,
-        "handles-missing-data": False,
+        "handles-missing-data": True,
         "capability:pred_int": True,
         "X-y-must-have-same-index": False,
     }
@@ -727,7 +726,6 @@ def __init__(self, steps):
         tags_to_clone = [
             "ignores-exogeneous-X",  # does estimator ignore the exogeneous X?
             "capability:pred_int",  # can the estimator produce prediction intervals?
-            "handles-missing-data",  # can estimator handle missing data?
             "requires-fh-in-fit",  # is forecasting horizon already required in fit?
             "enforce_index_type",  # index type that needs to be enforced in X/y
         ]
```

## Moved from `brief.md`

## Files That May Need Changes

- `sktime/forecasting/compose/_pipeline.py`
