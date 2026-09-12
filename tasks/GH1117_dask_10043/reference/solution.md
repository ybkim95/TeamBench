# Reference solution — GH1117_dask_10043

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1117_dask_10043`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1117_dask_10043/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `dask/dataframe/groupby.py` (modified, +1/-5)
- `dask/dataframe/shuffle.py` (modified, +1/-0)
- `dask/dataframe/tests/test_groupby.py` (modified, +38/-0)

## Diff Summary (What the Fix Changes)

### `dask/dataframe/groupby.py`
```diff
@@ -35,7 +35,6 @@
 )
 from dask.dataframe.dispatch import grouper_dispatch
 from dask.dataframe.methods import concat, drop_columns
-from dask.dataframe.shuffle import shuffle
 from dask.dataframe.utils import (
     insert_meta_param_description,
     is_dataframe_like,
@@ -1742,15 +1741,12 @@ def _shuffle(self, meta):
 
         if isinstance(self.by, DataFrame):  # add by columns to dataframe
             df2 = df.assign(**{"_by_" + c: self.by[c] for c in self.by.columns})
-            by = self.by
         elif isinstance(self.by, Series):
             df2 = df.assign(_by=self.by)
-            by = self.by
         else:
             df2 = df
-            by = df._select_columns_or_index(self.by)
 
-        df3 = shuffle(df2, by)  # shuffle dataframe and index
+        df3 = df2.shuffle(on=self.by)  # shuffle dataframe and index
 
         if isinstance(self.by, DataFrame):
             # extract by from dataframe
```

### `dask/dataframe/shuffle.py`
```diff
@@ -371,6 +371,7 @@ def shuffle(
     shuffle_disk
     """
     list_like = pd.api.types.is_list_like(index) and not is_dask_collection(index)
+    shuffle = shuffle or get_default_shuffle_algorithm()
     if shuffle == "tasks" and (isinstance(index, str) or list_like):
         # Avoid creating the "_partitions" column if possible.
         # We currently do this if the user is passing in
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `dask/dataframe/groupby.py`
- `dask/dataframe/shuffle.py`
