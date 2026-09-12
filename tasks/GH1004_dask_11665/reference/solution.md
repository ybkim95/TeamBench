# Reference solution — GH1004_dask_11665

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1004_dask_11665`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1004_dask_11665/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `dask/dataframe/io/parquet/arrow.py` (modified, +14/-3)
- `dask/dataframe/io/tests/test_parquet.py` (modified, +42/-0)

## Diff Summary (What the Fix Changes)

### `dask/dataframe/io/parquet/arrow.py`
```diff
@@ -1,5 +1,6 @@
 from __future__ import annotations
 
+import itertools
 import json
 import operator
 import textwrap
@@ -284,9 +285,19 @@ def _get_rg_statistics(row_group, col_names):
     statistics for all columns.
     """
 
-    row_group_schema = {
-        col_name: i for i, col_name in enumerate(row_group.schema.names)
-    }
+    row_group_schema = dict(
+        zip(
+            row_group.schema.names,
+            itertools.accumulate(
+                [
+                    # Need to account for multi-field struct columns
+                    max(row_group.schema.types[i].num_fields, 1)
+                    for i in range(len(row_group.schema.names) - 1)
+                ],
+                initial=0,
+            ),
+        )
+    )
 
     def name_stats(column_name):
         col = row_group.metadata.column(row_group_schema[column_name])
```

## Moved from `brief.md`

## Files That May Need Changes

- `dask/dataframe/io/parquet/arrow.py`
