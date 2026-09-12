# Reference solution — GH1005_ray_60236

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1005_ray_60236`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1005_ray_60236/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `python/ray/data/_internal/datasource/parquet_datasource.py` (modified, +5/-1)
- `python/ray/data/tests/datasource/test_parquet.py` (modified, +39/-0)

## Diff Summary (What the Fix Changes)

### `python/ray/data/_internal/datasource/parquet_datasource.py`
```diff
@@ -616,7 +616,11 @@ def _get_partition_columns(self) -> Optional[List[str]]:
             return None
 
         if not self._partition_columns:
-            return None
+            # If a projection is active but the dataset has no partition columns,
+            # then no partition columns should be included in the output.
+            # Returning [] ensures that no partition columns are added,
+            # `None` is interpreted as including all partition columns.
+            return []
 
         # Extract partition columns that are in the projection map
         partition_cols = [
```

## Moved from `brief.md`

## Files That May Need Changes

- `python/ray/data/_internal/datasource/parquet_datasource.py`
