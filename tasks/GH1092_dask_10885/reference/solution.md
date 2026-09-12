# Reference solution — GH1092_dask_10885

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1092_dask_10885`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1092_dask_10885/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `dask/array/routines.py` (modified, +10/-15)
- `dask/array/tests/test_routines.py` (modified, +16/-0)

## Diff Summary (What the Fix Changes)

### `dask/array/routines.py`
```diff
@@ -2056,24 +2056,19 @@ def _isnonzero_vec(v):
 _isnonzero_vec = np.vectorize(_isnonzero_vec, otypes=[bool])
 
 
+def _isnonzero(a):
+    # Output of np.vectorize can't be pickled
+    return _isnonzero_vec(a)
+
+
 def isnonzero(a):
-    if a.dtype.kind in {"U", "S"}:
-        # NumPy treats all-whitespace strings as falsy (like in `np.nonzero`).
-        # but not in `.astype(bool)`. To match the behavior of numpy at least until
-        # 1.19, we use `_isnonzero_vec`. When NumPy changes behavior, we should just
-        # use the try block below.
-        # https://github.com/numpy/numpy/issues/9875
-        return a.map_blocks(_isnonzero_vec, dtype=bool)
+    """Handle special cases where conversion to bool does not work correctly.
+    xref: https://github.com/numpy/numpy/issues/9479
+    """
     try:
-        np.zeros(tuple(), dtype=a.dtype).astype(bool)
+        np.zeros([], dtype=a.dtype).astype(bool)
     except ValueError:
-        ######################################################
-        # Handle special cases where conversion to bool does #
-        # not work correctly.                                #
-        #                                                    #
-        # xref: https://github.com/numpy/numpy/issues/9479   #
-        ######################################################
-        return a.map_blocks(_isnonzero_vec, dtype=bool)
+        return a.map_blocks(_isnonzero, dtype=bool)
     else:
         return a.astype(bool)
 
```

## Moved from `brief.md`

## Files That May Need Changes

- `dask/array/routines.py`
