# Reference solution — GH1143_dask_9570

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1143_dask_9570`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1143_dask_9570/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `dask/dataframe/core.py` (modified, +26/-19)
- `dask/dataframe/tests/test_dataframe.py` (modified, +34/-0)
- `dask/dataframe/tests/test_utils_dataframe.py` (modified, +32/-0)
- `dask/dataframe/utils.py` (modified, +46/-0)

## Diff Summary (What the Fix Changes)

### `dask/dataframe/core.py`
```diff
@@ -62,6 +62,8 @@
     is_index_like,
     is_series_like,
     make_meta,
+    meta_frame_constructor,
+    meta_series_constructor,
     raise_on_meta_error,
     valid_divisions,
 )
@@ -2482,8 +2484,8 @@ def _convert_time_cols_to_numeric(self, time_cols, axis, meta, skipna):
             # since each standard deviation will just be NaN
             needs_time_conversion = False
             numeric_dd = from_pandas(
-                pd.DataFrame(
-                    {"_": pd.Series([np.nan])},
+                meta_frame_constructor(self)(
+                    {"_": meta_series_constructor(self)([np.nan])},
                     index=self.index,
                 ),
                 npartitions=self.npartitions,
@@ -2813,7 +2815,7 @@ def quantile(self, q=0.5, axis=0, numeric_only=True, method="default"):
                 graph = HighLevelGraph.from_collections(
                     keyname, layer, dependencies=quantiles
                 )
-                return DataFrame(graph, keyname, meta, quantiles[0].divisions)
+                return new_dd_object(graph, keyname, meta, quantiles[0].divisions)
 
     @derived_from(pd.DataFrame)
     def describe(
@@ -3062,7 +3064,7 @@ def _cum_agg(
                 _take_last,
                 cumpart,
                 skipna,
-                meta=pd.Series([], dtype="float"),
+                meta=meta_series_constructor(self)([], dtype="float"),
                 token=name2,
             )
 
@@ -3260,7 +3262,7 @@ def dot(self, other, meta=no_default):
         def _dot_series(*args, **kwargs):
             # .sum() is invoked on each partition before being applied to all
             # partitions. The return type is expected to be a series, not a numpy object
-            return pd.Series(M.dot(*args, **kwargs))
+            return meta_series_constructor(self)(M.dot(*args, **kwargs))
 
         return self.map_partitions(_dot_series, other, token="dot", meta=meta).sum(
             skipna=False
@@ -3532,7 +3534,7 @@ def
```

### `dask/dataframe/utils.py`
```diff
@@ -734,3 +734,49 @@ def drop_by_shallow_copy(df, columns, errors="raise"):
 
 class AttributeNotImplementedError(NotImplementedError, AttributeError):
     """NotImplementedError and AttributeError"""
+
+
+def meta_frame_constructor(like):
+    """Return a serial DataFrame constructor
+
+    Parameters
+    ----------
+    like :
+        Any series-like, Index-like or dataframe-like object.
+    """
+    if is_dask_collection(like):
+        try:
+            like = like._meta
+        except AttributeError:
+            raise TypeError(f"{type(like)} not supported by meta_frame_constructor")
+    if is_dataframe_like(like):
+        return like._constructor
+    elif is_series_like(like):
+        return like._constructor_expanddim
+    elif is_index_like(like):
+        return like.to_frame()._constructor
+    else:
+        raise TypeError(f"{type(like)} not supported by meta_frame_constructor")
+
+
+def meta_series_constructor(like):
+    """Return a serial Series constructor
+
+    Parameters
+    ----------
+    like :
+        Any series-like, Index-like or dataframe-like object.
+    """
+    if is_dask_collection(like):
+        try:
+            like = like._meta
+        except AttributeError:
+            raise TypeError(f"{type(like)} not supported by meta_series_constructor")
+    if is_dataframe_like(like):
+        return like._constructor_sliced
+    elif is_series_like(like):
+        return like._constructor
+    elif is_index_like(like):
+        return like.to_frame()._constructor_sliced
+    else:
+        raise TypeError(f"{type(like)} not supported by meta_series_constructor")
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `dask/dataframe/core.py`
- `dask/dataframe/utils.py`
