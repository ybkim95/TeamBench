# Reference solution — GH959_scipy_24760

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH959_scipy_24760`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH959_scipy_24760/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `scipy/integrate/_ivp/common.py` (modified, +3/-3)
- `scipy/integrate/_ivp/tests/test_ivp.py` (modified, +16/-0)

## Diff Summary (What the Fix Changes)

### `scipy/integrate/_ivp/common.py`
```diff
@@ -385,7 +385,7 @@ def _dense_num_jac(fun, t, y, f, h, factor, y_scale):
 def _sparse_num_jac(fun, t, y, f, h, factor, y_scale, structure, groups):
     n = y.shape[0]
     n_groups = np.max(groups) + 1
-    h_vecs = np.empty((n_groups, n))
+    h_vecs = np.empty((n_groups, n), dtype=h.dtype)
     for group in range(n_groups):
         e = np.equal(group, groups)
         h_vecs[group] = h * e
@@ -407,12 +407,12 @@ def _sparse_num_jac(fun, t, y, f, h, factor, y_scale, structure, groups):
         ind, = np.nonzero(diff_too_small)
         new_factor = NUM_JAC_FACTOR_INCREASE * factor[ind]
         h_new = (y[ind] + new_factor * y_scale[ind]) - y[ind]
-        h_new_all = np.zeros(n)
+        h_new_all = np.zeros(n, dtype=h.dtype)
         h_new_all[ind] = h_new
 
         groups_unique = np.unique(groups[ind])
         groups_map = np.empty(n_groups, dtype=int)
-        h_vecs = np.empty((groups_unique.shape[0], n))
+        h_vecs = np.empty((groups_unique.shape[0], n), dtype=h.dtype)
         for k, group in enumerate(groups_unique):
             e = np.equal(group, groups)
             h_vecs[k] = h_new_all * e
```

## Moved from `brief.md`

## Files That May Need Changes

- `scipy/integrate/_ivp/common.py`
