# Reference solution — GH1071_dask_11656

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1071_dask_11656`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1071_dask_11656/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `dask/dataframe/dask_expr/_collection.py` (modified, +2/-0)
- `dask/dataframe/dask_expr/_indexing.py` (modified, +3/-0)
- `dask/dataframe/dask_expr/io/tests/test_io.py` (modified, +12/-0)
- `dask/dataframe/dask_expr/tests/test_groupby.py` (modified, +2/-5)
- `dask/dataframe/tests/test_groupby.py` (modified, +1/-4)

## Diff Summary (What the Fix Changes)

### `dask/dataframe/dask_expr/_collection.py`
```diff
@@ -416,6 +416,8 @@ def __getitem__(self, other):
             other = list(other)
         elif isinstance(other, list):
             other = other.copy()
+        elif isinstance(other, np.generic):
+            other = other.item()
         return new_collection(self.expr.__getitem__(other))
 
     def __dask_tokenize__(self):
```

### `dask/dataframe/dask_expr/_indexing.py`
```diff
@@ -78,6 +78,9 @@ def __getitem__(self, key):
             iindexer = key
             cindexer = None
 
+        if isinstance(cindexer, np.generic):
+            cindexer = cindexer.item()
+
         return self._loc(iindexer, cindexer)
 
     def _loc(self, iindexer, cindexer):
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `dask/dataframe/dask_expr/_collection.py`
- `dask/dataframe/dask_expr/_indexing.py`
