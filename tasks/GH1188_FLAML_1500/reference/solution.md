# Reference solution — GH1188_FLAML_1500

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1188_FLAML_1500`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1188_FLAML_1500/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `flaml/automl/automl.py` (modified, +36/-1)
- `test/automl/test_multiclass.py` (modified, +28/-0)

## Diff Summary (What the Fix Changes)

### `flaml/automl/automl.py`
```diff
@@ -156,6 +156,10 @@ def custom_metric(
                 "pred_time": pred_time,
             }
         ```
+                **Note:** When passing a custom metric function, pass the function itself
+                (e.g., `metric=custom_metric`), not the result of calling it
+                (e.g., `metric=custom_metric(...)`). FLAML will call your function
+                internally during the training process.
             task: A string of the task type, e.g.,
                 'classification', 'regression', 'ts_forecast', 'rank',
                 'seq-classification', 'seq-regression', 'summarization',
@@ -370,6 +374,8 @@ def custom_metric(
         settings["n_splits"] = settings.get("n_splits", N_SPLITS)
         settings["auto_augment"] = settings.get("auto_augment", True)
         settings["metric"] = settings.get("metric", "auto")
+        # Validate that custom metric is callable if not a string
+        self._validate_metric_parameter(settings["metric"], allow_auto=True)
         settings["estimator_list"] = settings.get("estimator_list", "auto")
         settings["log_file_name"] = settings.get("log_file_name", "")
         settings["max_iter"] = settings.get("max_iter")  # no budget by default
@@ -462,6 +468,28 @@ def __setstate__(self, state):
                 except Exception:
                     mi.mlflow_client = None
 
+    @staticmethod
+    def _validate_metric_parameter(metric, allow_auto=True):
+        """Validate that the metric parameter is either a string or a callable function.
+
+        Args:
+            metric: The metric parameter to validate.
+            allow_auto: Whether to allow "auto" as a valid string value.
+
+        Raises:
+            ValueError: If metric is not a string or callable function.
+        """
+        if allow_auto and metric == "auto":
+            return
+        if not isinstance(metric, str) and not callable(metric):
+            raise ValueError(
+                f"The 'metric' parameter must be eit
```

## Moved from `brief.md`

## Files That May Need Changes

- `flaml/automl/automl.py`
