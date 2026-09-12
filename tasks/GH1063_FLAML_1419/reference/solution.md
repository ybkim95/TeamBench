# Reference solution — GH1063_FLAML_1419

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1063_FLAML_1419`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1063_FLAML_1419/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `flaml/automl/automl.py` (modified, +15/-0)
- `test/automl/test_max_iter_1.py` (added, +51/-0)

## Diff Summary (What the Fix Changes)

### `flaml/automl/automl.py`
```diff
@@ -2529,6 +2529,21 @@ def _search(self):
             self._selected = state = self._search_states[estimator]
             state.best_config_sample_size = self._state.data_size[0]
             state.best_config = state.init_config[0] if state.init_config else {}
+            self._track_iter = 0
+            self._config_history[self._track_iter] = (estimator, state.best_config, self._state.time_from_start)
+            self._best_iteration = self._track_iter
+            state.val_loss = getattr(state, "val_loss", float("inf"))
+            state.best_loss = getattr(state, "best_loss", float("inf"))
+            state.config = getattr(state, "config", state.best_config.copy())
+            state.metric_for_logging = getattr(state, "metric_for_logging", None)
+            state.sample_size = getattr(state, "sample_size", self._state.data_size[0])
+            state.learner_class = getattr(state, "learner_class", self._state.learner_classes.get(estimator))
+            if hasattr(self, "mlflow_integration") and self.mlflow_integration:
+                self.mlflow_integration.record_state(
+                    automl=self,
+                    search_state=state,
+                    estimator=estimator,
+                )
         elif self._use_ray is False and self._use_spark is False:
             self._search_sequential()
         else:
```

## Moved from `brief.md`

## Files That May Need Changes

- `flaml/automl/automl.py`
