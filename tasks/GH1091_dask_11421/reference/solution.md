# Reference solution — GH1091_dask_11421

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1091_dask_11421`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1091_dask_11421/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `dask/array/slicing.py` (modified, +1/-1)
- `dask/array/tests/test_cupy_slicing.py` (modified, +13/-0)

## Diff Summary (What the Fix Changes)

### `dask/array/slicing.py`
```diff
@@ -1338,7 +1338,7 @@ def parse_assignment_indices(indices, shape):
             # Index is an integer
             index = int(index)
 
-        elif isinstance(index, np.ndarray) or is_dask_collection(index):
+        elif is_arraylike(index) or is_dask_collection(index):
             # Index is 1-d array
             n_lists += 1
             if n_lists > 1:
```

## Moved from `brief.md`

## Files That May Need Changes

- `dask/array/slicing.py`
