# Reference solution — GH889_pandas_64788

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH889_pandas_64788`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH889_pandas_64788/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/source/whatsnew/v3.1.0.rst` (modified, +1/-0)
- `pandas/core/arrays/datetimes.py` (modified, +14/-2)
- `pandas/tests/indexes/datetimes/test_date_range.py` (modified, +32/-0)

## Diff Summary (What the Fix Changes)

### `pandas/core/arrays/datetimes.py`
```diff
@@ -553,8 +553,20 @@ def _generate_range(
             if not left_inclusive and not right_inclusive:
                 i8values = i8values[1:-1]
         else:
-            start_i8 = Timestamp(start)._value
-            end_i8 = Timestamp(end)._value
+            start_i8 = (
+                Timestamp(start)._value
+                if start is not None
+                else i8values[0]
+                if len(i8values)
+                else 0
+            )
+            end_i8 = (
+                Timestamp(end)._value
+                if end is not None
+                else i8values[-1]
+                if len(i8values)
+                else 0
+            )
             if not left_inclusive or not right_inclusive:
                 if not left_inclusive and len(i8values) and i8values[0] == start_i8:
                     i8values = i8values[1:]
```

## Moved from `brief.md`

## Files That May Need Changes

- `pandas/core/arrays/datetimes.py`
