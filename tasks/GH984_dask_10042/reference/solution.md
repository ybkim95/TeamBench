# Reference solution — GH984_dask_10042

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH984_dask_10042`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH984_dask_10042/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `dask/dataframe/io/parquet/core.py` (modified, +10/-4)
- `dask/dataframe/io/tests/test_parquet.py` (modified, +20/-1)

## Diff Summary (What the Fix Changes)

### `dask/dataframe/io/parquet/core.py`
```diff
@@ -1375,14 +1375,20 @@ def apply_conjunction(parts, statistics, conjunction):
                     out_statistics.append(stats)
                 else:
                     if (
-                        operator != "is not"
-                        and min is None
-                        and max is None
-                        and null_count
+                        # Must allow row-groups with "missing" stats
+                        (min is None and max is None and not null_count)
+                        # Check "is" and "is not" fiters first
                         or operator == "is"
                         and null_count
                         or operator == "is not"
                         and (not pd.isna(min) or not pd.isna(max))
+                        # Allow all-null row-groups if not fitering out nulls
+                        or operator != "is not"
+                        and min is None
+                        and max is None
+                        and null_count
+                        # Start conventional (non-null) fitering
+                        # (main/max cannot be None for remaining checks)
                         or operator in ("==", "=")
                         and min <= value <= max
                         or operator == "!="
```

## Moved from `brief.md`

## Files That May Need Changes

- `dask/dataframe/io/parquet/core.py`
