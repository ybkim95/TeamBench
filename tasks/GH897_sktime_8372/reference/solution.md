# Reference solution — GH897_sktime_8372

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH897_sktime_8372`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH897_sktime_8372/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `sktime/performance_metrics/forecasting/probabilistic/_classes.py` (modified, +3/-1)
- `sktime/performance_metrics/forecasting/probabilistic/tests/test_probabilistic_metrics.py` (modified, +36/-0)

## Diff Summary (What the Fix Changes)

### `sktime/performance_metrics/forecasting/probabilistic/_classes.py`
```diff
@@ -679,7 +679,9 @@ def _evaluate_by_index(self, y_true, y_pred, multioutput, **kwargs):
 
         y_true_np = np.tile(y_true_np, no_scores)
 
-        truth_array = (y_true_np > lower).astype(int) * (y_true_np < upper).astype(int)
+        truth_array = (y_true_np >= lower).astype(int) * (y_true_np <= upper).astype(
+            int
+        )
 
         out_df = pd.DataFrame(
             truth_array, columns=pd.MultiIndex.from_product([vars, scores])
```

## Moved from `brief.md`

## Files That May Need Changes

- `sktime/performance_metrics/forecasting/probabilistic/_classes.py`
