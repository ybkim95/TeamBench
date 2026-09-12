# Reference solution — GH955_pandas_64683

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH955_pandas_64683`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH955_pandas_64683/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/source/whatsnew/v3.0.2.rst` (modified, +1/-0)
- `pandas/core/array_algos/masked_reductions.py` (modified, +19/-6)
- `pandas/core/arrays/string_.py` (modified, +5/-1)
- `pandas/tests/arrays/string_/test_string.py` (modified, +18/-0)

## Diff Summary (What the Fix Changes)

### `pandas/core/array_algos/masked_reductions.py`
```diff
@@ -10,7 +10,10 @@
 
 import numpy as np
 
-from pandas._libs import missing as libmissing
+from pandas._libs import (
+    lib,
+    missing as libmissing,
+)
 
 from pandas.core.nanops import check_below_min_count
 
@@ -31,6 +34,7 @@ def _reductions(
     skipna: bool = True,
     min_count: int = 0,
     axis: AxisInt | None = None,
+    initial: object | lib.NoDefault = lib.no_default,
     **kwargs,
 ):
     """
@@ -50,7 +54,13 @@ def _reductions(
         The required number of valid values to perform the operation. If fewer than
         ``min_count`` non-NA values are present the result will be NA.
     axis : int, optional, default None
+    initial : scalar, optional
+        Starting value for the reduction. NumPy has a default value for most
+        data types, but for object-dtype arrays we need to specify it explicitly
     """
+    if initial is not lib.no_default:
+        kwargs["initial"] = initial
+
     if not skipna:
         if mask.any() or check_below_min_count(values.shape, None, min_count):
             return libmissing.NA
@@ -62,10 +72,6 @@ def _reductions(
         ):
             return libmissing.NA
 
-        if values.dtype == np.dtype(object):
-            # object dtype does not support `where` without passing an initial
-            values = values[~mask]
-            return func(values, axis=axis, **kwargs)
         return func(values, where=~mask, axis=axis, **kwargs)
 
 
@@ -76,9 +82,16 @@ def sum(
     skipna: bool = True,
     min_count: int = 0,
     axis: AxisInt | None = None,
+    initial: object | lib.NoDefault = lib.no_default,
 ):
     return _reductions(
-        np.sum, values=values, mask=mask, skipna=skipna, min_count=min_count, axis=axis
+        np.sum,
+        values=values,
+        mask=mask,
+        skipna=skipna,
+        min_count=min_count,
+        axis=axis,
+        initial=initial,
     )
 
 
```

### `pandas/core/arrays/string_.py`
```diff
@@ -1079,7 +1079,11 @@ def sum(
     ) -> Scalar:
         nv.validate_sum((), kwargs)
         result = masked_reductions.sum(
-            values=self._ndarray, mask=self.isna(), skipna=skipna
+            values=self._ndarray,
+            mask=self.isna(),
+            skipna=skipna,
+            min_count=min_count,
+            initial="",
         )
         return self._wrap_reduction_result(axis, result)
 
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `pandas/core/array_algos/masked_reductions.py`
- `pandas/core/arrays/string_.py`
