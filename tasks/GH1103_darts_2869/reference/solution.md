# Reference solution — GH1103_darts_2869

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1103_darts_2869`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1103_darts_2869/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CHANGELOG.md` (modified, +1/-0)
- `darts/models/forecasting/forecasting_model.py` (modified, +1/-1)
- `darts/tests/utils/historical_forecasts/test_historical_forecasts.py` (modified, +93/-66)
- `darts/utils/historical_forecasts/utils.py` (modified, +3/-8)

## Diff Summary (What the Fix Changes)

### `darts/models/forecasting/forecasting_model.py`
```diff
@@ -1111,7 +1111,7 @@ def retrain_func(
             )
 
             # adjust the start of the series depending on whether we train (at some point), or predict only
-            # must be performed after the operation on historical_foreacsts_time_index
+            # must be performed after the operation on historical_forecasts_time_index
             if min_timestamp_series > series_.time_index[0]:
                 series_ = series_.drop_before(min_timestamp_series - 1 * series_.freq)
 
```

### `darts/utils/historical_forecasts/utils.py`
```diff
@@ -681,10 +681,7 @@ def _get_historical_forecastable_time_index(
 
     # longest possible time index for target
     if is_training:
-        start = (
-            series.start_time()
-            + (output_lag - output_chunk_shift - min_target_lag + 1) * series.freq
-        )
+        start = series.start_time() + (output_lag - min_target_lag + 1) * series.freq
     else:
         start = series.start_time() - min_target_lag * series.freq
     end = series.end_time() + 1 * series.freq
@@ -696,8 +693,7 @@ def _get_historical_forecastable_time_index(
         if is_training:
             start_pc = (
                 past_covariates.start_time()
-                + (output_lag - output_chunk_shift - min_past_cov_lag + 1)
-                * past_covariates.freq
+                + (output_lag - min_past_cov_lag + 1) * past_covariates.freq
             )
         else:
             start_pc = (
@@ -720,8 +716,7 @@ def _get_historical_forecastable_time_index(
         if is_training:
             start_fc = (
                 future_covariates.start_time()
-                + (output_lag - output_chunk_shift - min_future_cov_lag + 1)
-                * future_covariates.freq
+                + (output_lag - min_future_cov_lag + 1) * future_covariates.freq
             )
         else:
             start_fc = (
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `darts/models/forecasting/forecasting_model.py`
- `darts/utils/historical_forecasts/utils.py`
