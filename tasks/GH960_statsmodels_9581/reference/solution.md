# Reference solution — GH960_statsmodels_9581

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH960_statsmodels_9581`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH960_statsmodels_9581/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `statsmodels/genmod/families/family.py` (modified, +1/-1)
- `statsmodels/genmod/families/tests/test_family.py` (modified, +14/-2)

## Diff Summary (What the Fix Changes)

### `statsmodels/genmod/families/family.py`
```diff
@@ -1053,7 +1053,7 @@ def loglike_obs(self, endog, mu, var_weights=1., scale=1.):
         # note that mu is still in (0,1), i.e. not converted back
         return (
             special.gammaln(n + 1) - special.gammaln(y + 1) -
-            special.gammaln(n - y + 1) + y * np.log(mu / (1 - mu + 1e-20)) +
+            special.gammaln(n - y + 1) + y * np.log((mu + 1e-20) / (1 - mu + 1e-20)) +
             n * np.log(1 - mu + 1e-20)) * var_weights
 
     def resid_anscombe(self, endog, mu, var_weights=1., scale=1.):
```

## Moved from `brief.md`

## Files That May Need Changes

- `statsmodels/genmod/families/family.py`
