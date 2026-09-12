# Reference solution — GH1039_darts_2776

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1039_darts_2776`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1039_darts_2776/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `darts/models/forecasting/catboost_model.py` (modified, +1/-0)
- `darts/models/forecasting/regression_model.py` (modified, +3/-3)
- `darts/tests/models/forecasting/test_regression_models.py` (modified, +22/-3)

## Diff Summary (What the Fix Changes)

### `darts/models/forecasting/catboost_model.py`
```diff
@@ -374,6 +374,7 @@ def _add_val_set_to_kwargs(
                     data=val_set[0],
                     label=val_set[1],
                     weight=val_weights[i] if val_weights is not None else None,
+                    cat_features=self._categorical_indices,
                 )
             )
         kwargs[val_set_name] = val_pools
```

### `darts/models/forecasting/regression_model.py`
```diff
@@ -677,6 +677,8 @@ def _create_lagged_data(
         ):
             sample_weights = sample_weights.ravel()
 
+        features, labels = self._format_samples(features, labels)
+
         return features, labels, sample_weights
 
     def _format_samples(
@@ -733,9 +735,7 @@ def _fit_model(
                     "`sample_weight` was ignored since underlying regression model's "
                     "`fit()` method does not support it."
                 )
-        training_samples, training_labels = self._format_samples(
-            training_samples, training_labels
-        )
+
         self.model.fit(
             training_samples, training_labels, **sample_weight_kwargs, **kwargs
         )
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `darts/models/forecasting/catboost_model.py`
- `darts/models/forecasting/regression_model.py`
