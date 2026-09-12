# Reference solution — GH950_sktime_2375

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH950_sktime_2375`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH950_sktime_2375/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `sktime/datatypes/_panel/_convert.py` (modified, +14/-47)
- `sktime/datatypes/_series/_convert.py` (modified, +2/-2)
- `sktime/transformations/panel/segment.py` (modified, +4/-3)
- `sktime/transformations/panel/tests/test_segment.py` (modified, +15/-10)

## Diff Summary (What the Fix Changes)

### `sktime/datatypes/_panel/_convert.py`
```diff
@@ -683,8 +683,8 @@ def from_multi_index_to_nested(
     multi_ind_dataframe : pd.DataFrame
         Input multi-indexed pandas DataFrame
 
-    instance_index_name : str
-        The name of multi-index level corresponding to the DataFrame's instances
+    instance_index_name : int or str, default=0 (first level = 0-th index)
+        Index or name of multi-index level corresponding to the DataFrame's instances
 
     cells_as_numpy : bool, default = False
         If True, then nested cells contain NumPy array
@@ -764,54 +764,21 @@ def from_nested_to_multi_index(X, instance_index=None, time_index=None):
         The multi-indexed pandas DataFrame
 
     """
-    if time_index is None:
-        time_index_name = "timepoints"
-    else:
-        time_index_name = time_index
+    # this contains the right values, but does not have the right index
+    #   need convert_dtypes or dtypes will always be object
+    # explode by column to ensure we deal with unequal length series properly
+    X_mi = pd.DataFrame()
 
-    # n_columns = X.shape[1]
-    nested_col_mask = [*are_columns_nested(X)]
+    for c in X.columns:
+        X_col = X[[c]].explode(c)
+        X_col = X_col.infer_objects()
 
-    if instance_index is None:
-        instance_idxs = X.index.get_level_values(-1).unique()
-        # n_instances = instance_idxs.shape[0]
-        instance_index_name = "instance"
-
-    else:
-        if instance_index in X.index.names:
-            instance_idxs = X.index.get_level_values(instance_index).unique()
-        else:
-            instance_idxs = X.index.get_level_values(-1).unique()
-        # n_instances = instance_idxs.shape[0]
-        instance_index_name = instance_index
-
-    instances = []
-    for instance_idx in instance_idxs:
-        iidx = instance_idx
-        series = [i[1] for i in X.loc[iidx, :].iteritems()]
-        colnames = [i[0] for i in X.loc[iidx, :].iteritems()]
-        for x in series:
-            if hasattr(x, "name"):
-                x.
```

### `sktime/datatypes/_series/_convert.py`
```diff
@@ -100,7 +100,7 @@ def convert_MvS_to_np_as_Series(obj: pd.DataFrame, store=None) -> np.ndarray:
         store["columns"] = obj.columns
         store["index"] = obj.index
 
-    return obj.to_numpy()
+    return obj.to_numpy(dtype="float")
 
 
 convert_dict[("pd.DataFrame", "np.ndarray", "Series")] = convert_MvS_to_np_as_Series
@@ -114,7 +114,7 @@ def convert_UvS_to_np_as_Series(obj: pd.Series, store=None) -> np.ndarray:
     if isinstance(store, dict):
         store["index"] = obj.index
 
-    return pd.DataFrame(obj).to_numpy()
+    return pd.DataFrame(obj).to_numpy(dtype="float")
 
 
 convert_dict[("pd.Series", "np.ndarray", "Series")] = convert_UvS_to_np_as_Series
```

### `sktime/transformations/panel/segment.py`
```diff
@@ -125,9 +125,10 @@ def _transform(self, X, y=None):
         new_column_names = []
         for interval in self.intervals_:
             start, end = interval[0], interval[-1]
-            interval = X[:, start:end]
-            intervals.append(interval)
-            new_column_names.append(f"{column_names}_{start}_{end}")
+            if f"{column_names}_{start}_{end}" not in new_column_names:
+                interval = X[:, start:end]
+                intervals.append(interval)
+                new_column_names.append(f"{column_names}_{start}_{end}")
 
         # Return nested pandas DataFrame.
         Xt = pd.DataFrame(_concat_nested_arrays(intervals))
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `sktime/datatypes/_panel/_convert.py`
- `sktime/datatypes/_series/_convert.py`
- `sktime/transformations/panel/segment.py`
