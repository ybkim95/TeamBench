# Reference solution — GH1134_darts_2887

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1134_darts_2887`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1134_darts_2887/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CHANGELOG.md` (modified, +17/-17)
- `darts/tests/models/forecasting/test_ensemble_models.py` (modified, +15/-15)
- `darts/tests/models/forecasting/test_probabilistic_models.py` (modified, +6/-6)
- `darts/tests/models/forecasting/test_regression_ensemble_model.py` (modified, +15/-13)
- `darts/tests/models/forecasting/test_sf_models.py` (modified, +1/-1)
- `darts/tests/models/forecasting/test_sklearn_models.py` (modified, +1/-1)
- `darts/tests/utils/historical_forecasts/test_historical_forecasts.py` (modified, +1/-1)
- `darts/tests/utils/test_utils.py` (modified, +8/-8)
- `darts/timeseries.py` (modified, +1/-1)
- `darts/utils/likelihood_models/base.py` (modified, +4/-4)

## Diff Summary (What the Fix Changes)

### `darts/timeseries.py`
```diff
@@ -4783,7 +4783,7 @@ def quantile(self, q: Union[float, Sequence[float]] = 0.5, **kwargs) -> Self:
             )
 
         # component names
-        cnames = [f"{comp}_q{q_i:.2f}" for comp in self.components for q_i in q]
+        cnames = [f"{comp}_q{q_i:.3f}" for comp in self.components for q_i in q]
 
         # get quantiles of shape (n quantiles, n times, n components)
         new_data = np.quantile(self._values, q=q, axis=2, **kwargs)
```

### `darts/utils/likelihood_models/base.py`
```diff
@@ -157,9 +157,9 @@ def quantile_names(q: Union[float, list[float]], component: Optional[str] = None
     # predicted quantile text format
     comp = f"{component}_" if component is not None else ""
     if isinstance(q, float):
-        return f"{comp}q{q:.2f}"
+        return f"{comp}q{q:.3f}"
     else:
-        return [f"{comp}q{q_i:.2f}" for q_i in q]
+        return [f"{comp}q{q_i:.3f}" for q_i in q]
 
 
 def quantile_interval_names(
@@ -178,6 +178,6 @@ def quantile_interval_names(
     # predicted quantile text format
     comp = f"{component}_" if component is not None else ""
     if isinstance(q_interval, tuple):
-        return f"{comp}q{q_interval[0]:.2f}_q{q_interval[1]:.2f}"
+        return f"{comp}q{q_interval[0]:.3f}_q{q_interval[1]:.3f}"
     else:
-        return [f"{comp}q{q_lo:.2f}_q{q_hi:.2f}" for q_lo, q_hi in q_interval]
+        return [f"{comp}q{q_lo:.3f}_q{q_hi:.3f}" for q_lo, q_hi in q_interval]
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `darts/timeseries.py`
- `darts/utils/likelihood_models/base.py`
