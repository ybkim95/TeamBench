# Reference solution — GH1171_FLAML_1469

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1171_FLAML_1469`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1171_FLAML_1469/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `flaml/automl/ml.py` (modified, +6/-1)
- `flaml/automl/time_series/tcn.py` (modified, +2/-1)
- `flaml/automl/time_series/tft.py` (modified, +5/-1)
- `flaml/automl/time_series/ts_model.py` (modified, +30/-3)
- `test/automl/test_forecast.py` (modified, +45/-1)

## Diff Summary (What the Fix Changes)

### `flaml/automl/ml.py`
```diff
@@ -616,7 +616,12 @@ def _eval_estimator(
             logger.warning(f"ValueError {e} happened in `metric_loss_score`, set `val_loss` to `np.inf`")
         metric_for_logging = {"pred_time": pred_time}
         if log_training_metric:
-            train_pred_y = get_y_pred(estimator, X_train, eval_metric, task)
+            # For time series forecasting, X_train may be a sampled dataset whose
+            # test partition can be empty. Use the training partition from X_val
+            # (which is the dataset used to define y_train above) to keep shapes
+            # aligned and avoid empty prediction inputs.
+            X_train_for_metric = X_val.X_train if isinstance(X_val, TimeSeriesDataset) else X_train
+            train_pred_y = get_y_pred(estimator, X_train_for_metric, eval_metric, task)
             metric_for_logging["train_loss"] = metric_loss_score(
                 eval_metric,
                 train_pred_y,
```

### `flaml/automl/time_series/tcn.py`
```diff
@@ -264,7 +264,8 @@ def fit(self, X_train: TimeSeriesDataset, y_train=None, budget=None, **kwargs):
     def predict(self, X):
         X = self.enrich(X)
         if isinstance(X, TimeSeriesDataset):
-            df = X.X_val
+            # Use X_train if X_val is empty (e.g., when computing training metrics)
+            df = X.X_val if len(X.test_data) > 0 else X.X_train
         else:
             df = X
         dataset = DataframeDataset(
```

### `flaml/automl/time_series/tft.py`
```diff
@@ -197,7 +197,11 @@ def predict(self, X):
         last_data_cols = self.group_ids.copy()
         last_data_cols.append(self.target_names[0])
         last_data = self.data[lambda x: x.time_idx == x.time_idx.max()][last_data_cols]
-        decoder_data = X.X_val if isinstance(X, TimeSeriesDataset) else X
+        # Use X_train if test_data is empty (e.g., when computing training metrics)
+        if isinstance(X, TimeSeriesDataset):
+            decoder_data = X.X_val if len(X.test_data) > 0 else X.X_train
+        else:
+            decoder_data = X
         if "time_idx" not in decoder_data:
             decoder_data = add_time_idx_col(decoder_data)
         decoder_data["time_idx"] += encoder_data["time_idx"].max() + 1 - decoder_data["time_idx"].min()
```

### `flaml/automl/time_series/ts_model.py`
```diff
@@ -194,7 +194,13 @@ def predict(self, X: Union[TimeSeriesDataset, DataFrame], **kwargs):
 
         elif isinstance(X, TimeSeriesDataset):
             data = X
-            X = data.test_data[[self.time_col] + X.regressors]
+            # By default we predict on the dataset's test partition.
+            # Some internal call paths (e.g., training-metric logging) may pass a
+            # dataset whose test partition is empty; fall back to train partition.
+            if data.test_data is not None and len(data.test_data):
+                X = data.test_data[data.regressors + [data.time_col]]
+            else:
+                X = data.train_data[data.regressors + [data.time_col]]
 
         if self._model is not None:
             forecast = self._model.predict(X, **kwargs)
@@ -301,7 +307,13 @@ def predict(self, X, **kwargs):
 
         if isinstance(X, TimeSeriesDataset):
             data = X
-            X = data.test_data[data.regressors + [data.time_col]]
+            # By default we predict on the dataset's test partition.
+            # Some internal call paths (e.g., training-metric logging) may pass a
+            # dataset whose test partition is empty; fall back to train partition.
+            if data.test_data is not None and len(data.test_data):
+                X = data.test_data[data.regressors + [data.time_col]]
+            else:
+                X = data.train_data[data.regressors + [data.time_col]]
 
         X = X.rename(columns={self.time_col: "ds"})
         if self._model is not None:
@@ -327,11 +339,19 @@ def predict(self, X, **kwargs) -> pd.Series:
 
         if isinstance(X, TimeSeriesDataset):
             data = X
-            X = data.test_data[data.regressors + [data.time_col]]
+            # By default we predict on the dataset's test partition.
+            # Some internal call paths (e.g., training-metric logging) may pass a
+            # dataset whose test partition is empty; fall back to train partition.
+            if data.
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `flaml/automl/ml.py`
- `flaml/automl/time_series/tcn.py`
- `flaml/automl/time_series/tft.py`
- `flaml/automl/time_series/ts_model.py`
