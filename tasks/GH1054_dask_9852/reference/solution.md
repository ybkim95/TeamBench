# Reference solution — GH1054_dask_9852

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1054_dask_9852`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1054_dask_9852/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `dask/dataframe/multi.py` (modified, +1/-1)
- `dask/dataframe/tests/test_multi.py` (modified, +12/-1)

## Diff Summary (What the Fix Changes)

### `dask/dataframe/multi.py`
```diff
@@ -674,7 +674,7 @@ def merge(
         n_small = min(left.npartitions, right.npartitions)
         n_big = max(left.npartitions, right.npartitions)
         if (
-            shuffle == "tasks"
+            shuffle in ("tasks", None)
             and how in ("inner", "left", "right")
             and how != bcast_side
             and broadcast is not False
```

## Moved from `brief.md`

## Files That May Need Changes

- `dask/dataframe/multi.py`
