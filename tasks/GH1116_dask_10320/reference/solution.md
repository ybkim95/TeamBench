# Reference solution — GH1116_dask_10320

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1116_dask_10320`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1116_dask_10320/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `dask/dataframe/io/parquet/core.py` (modified, +25/-1)
- `dask/dataframe/io/tests/test_parquet.py` (modified, +16/-0)

## Diff Summary (What the Fix Changes)

### `dask/dataframe/io/parquet/core.py`
```diff
@@ -1347,9 +1347,31 @@ def apply_filters(parts, statistics, filters):
     parts, statistics: the same as the input, but possibly a subset
     """
 
+    # Supported predicate operators
+    _supported_operators = {
+        "=",
+        "==",
+        "!=",
+        "<",
+        "<=",
+        ">",
+        ">=",
+        "is",
+        "is not",
+        "in",
+        "not in",
+    }
+
     def apply_conjunction(parts, statistics, conjunction):
         for column, operator, value in conjunction:
-            if operator == "in" and not isinstance(value, (list, set, tuple)):
+            if operator not in _supported_operators:
+                # Use same error message as `_filters_to_expression`
+                raise ValueError(
+                    f'"{(column, operator, value)}" is not a valid operator in predicates.'
+                )
+            elif operator in ("in", "not in") and not isinstance(
+                value, (list, set, tuple)
+            ):
                 raise TypeError("Value of 'in' filter must be a list, set, or tuple.")
             out_parts = []
             out_statistics = []
@@ -1394,6 +1416,8 @@ def apply_conjunction(parts, statistics, conjunction):
                         and max >= value
                         or operator == "in"
                         and any(min <= item <= max for item in value)
+                        or operator == "not in"
+                        and not any(min == max == item for item in value)
                     ):
                         out_parts.append(part)
                         out_statistics.append(stats)
```

## Moved from `brief.md`

## Files That May Need Changes

- `dask/dataframe/io/parquet/core.py`
