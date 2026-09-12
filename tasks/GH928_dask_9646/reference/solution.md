# Reference solution — GH928_dask_9646

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH928_dask_9646`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH928_dask_9646/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `dask/dataframe/groupby.py` (modified, +3/-1)
- `dask/dataframe/tests/test_groupby.py` (modified, +5/-0)

## Diff Summary (What the Fix Changes)

### `dask/dataframe/groupby.py`
```diff
@@ -1950,7 +1950,9 @@ def aggregate(
 
             # Check if the aggregation involves implicit column projection
             if isinstance(arg, dict):
-                column_projection = group_columns | arg.keys()
+                column_projection = group_columns.union(arg.keys()).intersection(
+                    self.obj.columns
+                )
 
         elif isinstance(self.obj, Series):
             if isinstance(arg, (list, tuple, dict)):
```

## Moved from `brief.md`

## Files That May Need Changes

- `dask/dataframe/groupby.py`
