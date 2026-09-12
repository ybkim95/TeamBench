# Reference solution — GH1051_scipy_24742

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1051_scipy_24742`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1051_scipy_24742/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `scipy/stats/_stats_py.py` (modified, +1/-7)
- `scipy/stats/tests/test_stats.py` (modified, +30/-9)

## Diff Summary (What the Fix Changes)

### `scipy/stats/_stats_py.py`
```diff
@@ -10868,13 +10868,7 @@ def linregress(x, y, alternative='two-sided', *, axis=0):
 
     slope = ssxym / ssxm
     intercept = ymean - slope*xmean
-    if not is_marray(xp) and n == 2:
-        # handle case when only two points are passed in
-        one = xp.asarray(1.0, dtype=r.dtype)
-        prob = xp.where(y[..., 0] == y[..., 1], one, 0.0)
-        slope_stderr = xp.zeros_like(r)
-        intercept_stderr = xp.zeros_like(r)
-    else:
+    with np.errstate(invalid='ignore', divide='ignore'):
         df = n - 2  # Number of degrees of freedom
         # n-2 degrees of freedom because 2 has been used up
         # to estimate the mean and standard deviation
```

## Moved from `brief.md`

## Files That May Need Changes

- `scipy/stats/_stats_py.py`
