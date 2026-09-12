# Reference solution — GH1062_autogluon_5436

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1062_autogluon_5436`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1062_autogluon_5436/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `timeseries/src/autogluon/timeseries/models/abstract/abstract_timeseries_model.py` (modified, +10/-6)
- `timeseries/src/autogluon/timeseries/trainer/ensemble_composer.py` (modified, +21/-11)
- `timeseries/tests/unittests/trainer/test_ensemble_composer.py` (modified, +61/-0)

## Diff Summary (What the Fix Changes)

### `timeseries/src/autogluon/timeseries/models/abstract/abstract_timeseries_model.py`
```diff
@@ -122,12 +122,16 @@ def __init__(
         # user provided hyperparameters and extra arguments that are used during model training
         self._hyperparameters, self._extra_ag_args = self._check_and_split_hyperparameters(hyperparameters)
 
-        self.fit_time: float | None = None  # Time taken to fit in seconds (Training data)
-        self.predict_time: float | None = None  # Time taken to predict in seconds (Validation data)
-        self.predict_1_time: float | None = (
-            None  # Time taken to predict 1 row of data in seconds (with batch size `predict_1_batch_size`)
-        )
-        self.val_score: float | None = None  # Score with eval_metric (Validation data)
+        # Time taken to fit in seconds (Training data)
+        self.fit_time: float | None = None
+        # Time taken to predict in seconds, for a single prediction horizon on validation data
+        self.predict_time: float | None = None
+        # Time taken to predict 1 row of data in seconds (with batch size `predict_1_batch_size`)
+        self.predict_1_time: float | None = None
+        # Useful for ensembles, additional prediction time excluding base models. None for base models.
+        self.predict_time_marginal: float | None = None
+        # Score with eval_metric on validation data
+        self.val_score: float | None = None
 
     def __repr__(self) -> str:
         return self.name
```

### `timeseries/src/autogluon/timeseries/trainer/ensemble_composer.py`
```diff
@@ -253,10 +253,8 @@ def get_ground_truth_for_layer(layer_idx):
 
                         predict_time = time.monotonic() - predict_time_start
 
-                    # prediction time is last layer's time + base models
-                    ensemble.predict_time = predict_time + self._calculate_base_models_predict_time(
-                        ensemble.model_names
-                    )
+                    # record marginal prediction time per window in the last layer's data
+                    ensemble.predict_time_marginal = predict_time / self.num_windows_per_layer[-1]
                     ensemble.cache_oof_predictions(predictions)
 
                     # compute validation score using the last layer's validation windows
@@ -268,18 +266,20 @@ def get_ground_truth_for_layer(layer_idx):
                     ]
                     ensemble.val_score = float(np.mean(score_per_fold, dtype=np.float64))
 
-                    # log performance and save
+                    # add model to the graph, compute predict time, and save
+                    self._add_model(ensemble, base_models=ensemble.model_names)
+                    ensemble.predict_time = self._calculate_predict_time(ensemble)
+                    self.model_graph.nodes[ensemble.name]["predict_time"] = ensemble.predict_time
+                    ensemble.save()
+
+                    # log performance
                     log_scores_and_times(
                         ensemble.val_score,
                         ensemble.fit_time,
                         ensemble.predict_time,
                         eval_metric_name=self.eval_metric.name_with_sign,
                     )
 
-                    # save ensemble
-                    self._add_model(ensemble, base_models=ensemble.model_names)
-                    ensemble.save()
-
                     # check time and advance round
                     if main_loop_timer.timed_out():
                         logger.warning(
@@ -409,9 +409,19 @@ def _get
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `timeseries/src/autogluon/timeseries/models/abstract/abstract_timeseries_model.py`
- `timeseries/src/autogluon/timeseries/trainer/ensemble_composer.py`
