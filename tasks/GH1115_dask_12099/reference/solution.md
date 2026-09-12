# Reference solution — GH1115_dask_12099

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1115_dask_12099`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1115_dask_12099/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `dask/dataframe/dask_expr/_expr.py` (modified, +5/-1)
- `dask/dataframe/dask_expr/_groupby.py` (modified, +4/-1)
- `dask/dataframe/dask_expr/tests/test_groupby.py` (modified, +14/-0)

## Diff Summary (What the Fix Changes)

### `dask/dataframe/dask_expr/_expr.py`
```diff
@@ -593,7 +593,11 @@ def _divisions(self):
         dependencies = self.dependencies()
         for arg in dependencies:
             if not self._broadcast_dep(arg):
-                assert arg.divisions == dependencies[0].divisions
+                assert arg.divisions == dependencies[0].divisions, (
+                    "Mismatched divisions between multiple Blockwise dependencies. "
+                    f"Expected {dependencies[0].divisions}. Got {arg.divisions}. "
+                    "This may happen when a collection is passed to `meta=`."
+                )
         return dependencies[0].divisions
 
     @functools.cached_property
```

### `dask/dataframe/dask_expr/_groupby.py`
```diff
@@ -1025,7 +1025,10 @@ def get_map_columns(df):
             self.operand("args"),
             self.operand("kwargs"),
             grp_func,
-            self.operand("meta"),
+            # Make sure the meta argument isn't a collection.
+            # Blockwise may treat it as an Expr dependency.
+            # See: https://github.com/dask/dask/issues/11990
+            self._meta,
             *by,
         )
 
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `dask/dataframe/dask_expr/_expr.py`
- `dask/dataframe/dask_expr/_groupby.py`
