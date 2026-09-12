# Reference solution — GH870_pandas_64791

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH870_pandas_64791`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH870_pandas_64791/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/source/whatsnew/v3.1.0.rst` (modified, +1/-0)
- `pandas/core/nanops.py` (modified, +4/-2)
- `pandas/tests/frame/test_reductions.py` (modified, +4/-1)
- `pandas/tests/test_nanops.py` (modified, +10/-0)

## Diff Summary (What the Fix Changes)

### `pandas/core/nanops.py`
```diff
@@ -634,7 +634,8 @@ def nansum(
     values, mask = _get_values(values, skipna, fill_value=0, mask=mask)
     dtype_sum = _get_dtype_max(dtype)
     if dtype.kind == "f":
-        dtype_sum = dtype
+        # GH#43929 float16 sum overflows easily; upcast like numpy does
+        dtype_sum = np.dtype(np.float64) if dtype == np.float16 else dtype
     elif dtype.kind == "m":
         dtype_sum = np.dtype(np.float64)
 
@@ -708,7 +709,8 @@ def nanmean(
     elif dtype.kind in "iu":
         dtype_sum = np.dtype(np.float64)
     elif dtype.kind == "f":
-        dtype_sum = dtype
+        # GH#43929 float16 sum overflows easily; upcast like numpy does
+        dtype_sum = np.dtype(np.float64) if dtype == np.float16 else dtype
         dtype_count = dtype
 
     count = _get_counts(values.shape, mask, axis, dtype=dtype_count)
```

## Moved from `brief.md`

## Files That May Need Changes

- `pandas/core/nanops.py`
