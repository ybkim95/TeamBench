# Reference solution — GH914_darts_1652

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH914_darts_1652`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH914_darts_1652/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `darts/models/forecasting/forecasting_model.py` (modified, +4/-5)
- `darts/tests/models/forecasting/test_historical_forecasts.py` (modified, +6/-31)

## Diff Summary (What the Fix Changes)

### `darts/models/forecasting/forecasting_model.py`
```diff
@@ -478,7 +478,7 @@ def _get_historical_forecastable_time_index(
                 else future_covariates.start_time()
                 - min_future_cov_lag * future_covariates.freq,
                 end=future_covariates.end_time()
-                - max_future_cov_lag * future_covariates.freq,
+                - (max_future_cov_lag - 1) * future_covariates.freq,
                 freq=future_covariates.freq,
             )
 
@@ -559,7 +559,6 @@ def historical_forecasts(
     ) -> Union[
         TimeSeries, List[TimeSeries], Sequence[TimeSeries], Sequence[List[TimeSeries]]
     ]:
-
         """Compute the historical forecasts that would have been obtained by this model on
         (potentially multiple) `series`.
 
@@ -806,13 +805,15 @@ def historical_forecasts(
                         logger,
                     )
 
-            # build the prediction times in advance (to be able to use tqdm)
+            # Take into account overlap_end, and forecast_horizon.
             last_valid_pred_time = self._get_last_prediction_time(
                 series_,
                 forecast_horizon,
                 overlap_end,
             )
 
+            # The historical_forecasts_time_index end (which was just model dependent so far) is readjusted
+            # by function parameters overlap_end and forecast_horizon.
             historical_forecasts_time_index = drop_after_index(
                 historical_forecasts_time_index, last_valid_pred_time
             )
@@ -938,7 +939,6 @@ def backtest(
         reduction: Union[Callable[[np.ndarray], float], None] = np.mean,
         verbose: bool = False,
     ) -> Union[float, List[float], Sequence[float], List[Sequence[float]]]:
-
         """Compute error values that the model would have produced when
         used on (potentially multiple) `series`.
 
@@ -1608,7 +1608,6 @@ def load(path: Union[str, BinaryIO]) -> "ForecastingModel":
             with open(path, "rb") as handle:
                 model = pickle.load(file=
```

## Moved from `brief.md`

## Files That May Need Changes

- `darts/models/forecasting/forecasting_model.py`
