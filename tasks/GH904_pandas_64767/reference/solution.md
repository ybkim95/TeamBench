# Reference solution — GH904_pandas_64767

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH904_pandas_64767`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH904_pandas_64767/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/source/whatsnew/v3.1.0.rst` (modified, +1/-1)
- `pandas/core/indexes/multi.py` (modified, +16/-0)
- `pandas/tests/indexes/multi/test_sorting.py` (modified, +16/-0)

## Diff Summary (What the Fix Changes)

### `pandas/core/indexes/multi.py`
```diff
@@ -3188,6 +3188,22 @@ def sortlevel(
         ]
         sortorder = None
 
+        # Validate that levels being sorted have comparable types (GH#21136).
+        # Since we sort by integer codes rather than actual values, we need
+        # to ensure the level values are sortable; otherwise the code-based
+        # sort silently produces a meaningless ordering.
+        # After _sort_levels_monotonic (called before sortlevel in the
+        # standard path), a level that is still non-monotonic with object
+        # dtype must contain incomparable types.
+        for lev_num in level:
+            lev_values = self.levels[lev_num]
+            if (
+                lev_values.dtype == object
+                and not lev_values.is_monotonic_increasing
+                and not lev_values.is_monotonic_decreasing
+            ):
+                lev_values.argsort()
+
         codes = [self.codes[lev] for lev in level]
         # we have a directed ordering via ascending
         if isinstance(ascending, list):
```

## Moved from `brief.md`

## Files That May Need Changes

- `pandas/core/indexes/multi.py`
