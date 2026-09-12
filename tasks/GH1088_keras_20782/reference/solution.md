# Reference solution — GH1088_keras_20782

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1088_keras_20782`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1088_keras_20782/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `keras/src/metrics/reduction_metrics.py` (modified, +3/-0)
- `keras/src/metrics/reduction_metrics_test.py` (modified, +17/-0)

## Diff Summary (What the Fix Changes)

### `keras/src/metrics/reduction_metrics.py`
```diff
@@ -199,6 +199,9 @@ def __init__(self, fn, name=None, dtype=None, **kwargs):
             self._direction = "down"
 
     def update_state(self, y_true, y_pred, sample_weight=None):
+        y_true = backend.cast(y_true, self.dtype)
+        y_pred = backend.cast(y_pred, self.dtype)
+
         mask = backend.get_keras_mask(y_pred)
         values = self._fn(y_true, y_pred, **self._fn_kwargs)
         if sample_weight is not None and mask is not None:
```

## Moved from `brief.md`

## Files That May Need Changes

- `keras/src/metrics/reduction_metrics.py`
