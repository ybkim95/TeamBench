# Reference solution — GH1179_statsmodels_9673

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1179_statsmodels_9673`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1179_statsmodels_9673/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `statsmodels/genmod/generalized_estimating_equations.py` (modified, +1/-1)
- `statsmodels/regression/tests/test_lme.py` (modified, +1/-1)
- `statsmodels/stats/descriptivestats.py` (modified, +1/-1)

## Diff Summary (What the Fix Changes)

### `statsmodels/genmod/generalized_estimating_equations.py`
```diff
@@ -2938,7 +2938,7 @@ def setup_nominal(self, endog, exog, groups, time, offset):
                 u = np.zeros(len(endog_cuts), dtype=np.float64)
                 u[thresh_ix] = 1
                 exog_out[jrow, :] = np.kron(u, exog_row)
-                endog_out[jrow] = int(endog_value == thresh)
+                endog_out[jrow] = int(np.squeeze(endog_value == thresh))
                 groups_out[jrow] = group_value
                 time_out[jrow] = time_value
                 offset_out[jrow] = offset_value
```

### `statsmodels/stats/descriptivestats.py`
```diff
@@ -408,7 +408,7 @@ def _mode(ser):
             if np.isscalar(mode_res[0]):
                 return float(mode_res[0]), mode_res[1]
             if mode_res[0].shape[0] > 0:
-                return [float(val) for val in mode_res]
+                return [float(np.squeeze(val)) for val in mode_res]
             return np.nan, np.nan
 
         mode_values = df.apply(_mode).T
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `statsmodels/genmod/generalized_estimating_equations.py`
- `statsmodels/stats/descriptivestats.py`
