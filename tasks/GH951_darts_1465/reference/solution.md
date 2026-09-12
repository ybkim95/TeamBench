# Reference solution — GH951_darts_1465

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH951_darts_1465`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH951_darts_1465/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `darts/models/forecasting/forecasting_model.py` (modified, +11/-14)
- `darts/tests/models/forecasting/test_backtesting.py` (modified, +18/-1)
- `darts/tests/models/forecasting/test_ensemble_models.py` (modified, +7/-0)
- `examples/00-quickstart.ipynb` (modified, +237/-153)

## Diff Summary (What the Fix Changes)

### `darts/models/forecasting/forecasting_model.py`
```diff
@@ -691,17 +691,16 @@ def historical_forecasts(
             retrain_func = _retrain_wrapper(
                 lambda counter: counter % int(retrain) == 0 if retrain else False
             )
-
         elif isinstance(retrain, Callable):
             retrain_func = _retrain_wrapper(retrain)
-
         else:
             raise_log(
                 ValueError(
                     "`retrain` argument must be either `bool`, positive `int` or `Callable` (returning `bool`)"
                 ),
                 logger,
             )
+
         retrain_func_signature = tuple(
             inspect.signature(retrain_func).parameters.keys()
         )
@@ -728,7 +727,6 @@ def historical_forecasts(
 
         forecasts_list = []
         for idx, series_ in enumerate(outer_iterator):
-
             past_covariates_ = past_covariates[idx] if past_covariates else None
             future_covariates_ = future_covariates[idx] if future_covariates else None
 
@@ -765,15 +763,12 @@ def historical_forecasts(
 
             # prepare the start parameter -> pd.Timestamp
             if start is not None:
-
                 historical_forecasts_time_index = drop_before_index(
                     historical_forecasts_time_index,
                     series_.get_timestamp_at_point(start),
                 )
-
             else:
                 if (retrain is not False) or (not self._fit_called):
-
                     if train_length:
                         historical_forecasts_time_index = drop_before_index(
                             historical_forecasts_time_index,
@@ -804,9 +799,9 @@ def historical_forecasts(
                         (not self._fit_called)
                         and (retrain is False)
                         and (not train_length),
-                        " The model has not been fitted yet, and `start` and train_length are not specified. "
-                        " The model is not retraining during the historical forecasts. Hence the "
-                
```

## Moved from `brief.md`

## Files That May Need Changes

- `darts/models/forecasting/forecasting_model.py`
