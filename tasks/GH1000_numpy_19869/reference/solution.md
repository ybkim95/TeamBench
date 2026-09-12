# Reference solution — GH1000_numpy_19869

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1000_numpy_19869`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1000_numpy_19869/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `numpy/lib/function_base.py` (modified, +7/-8)
- `numpy/lib/tests/test_function_base.py` (modified, +10/-0)
- `numpy/lib/utils.py` (modified, +13/-15)
- `numpy/ma/extras.py` (modified, +2/-2)

## Diff Summary (What the Fix Changes)

### `numpy/lib/function_base.py`
```diff
@@ -3714,16 +3714,15 @@ def _median(a, axis=None, out=None, overwrite_input=False):
         indexer[axis] = slice(index-1, index+1)
     indexer = tuple(indexer)
 
+    # Use mean in both odd and even case to coerce data type,
+    # using out array if needed.
+    rout = mean(part[indexer], axis=axis, out=out)
     # Check if the array contains any nan's
     if np.issubdtype(a.dtype, np.inexact) and sz > 0:
-        # warn and return nans like mean would
-        rout = mean(part[indexer], axis=axis, out=out)
-        return np.lib.utils._median_nancheck(part, rout, axis, out)
-    else:
-        # if there are no nans
-        # Use mean in odd and even case to coerce data type
-        # and check, use out array.
-        return mean(part[indexer], axis=axis, out=out)
+        # If nans are possible, warn and replace by nans like mean would.
+        rout = np.lib.utils._median_nancheck(part, rout, axis)
+
+    return rout
 
 
 def _percentile_dispatcher(a, q, axis=None, out=None, overwrite_input=None,
```

### `numpy/lib/utils.py`
```diff
@@ -1002,41 +1002,39 @@ def safe_eval(source):
     return ast.literal_eval(source)
 
 
-def _median_nancheck(data, result, axis, out):
+def _median_nancheck(data, result, axis):
     """
     Utility function to check median result from data for NaN values at the end
     and return NaN in that case. Input result can also be a MaskedArray.
 
     Parameters
     ----------
     data : array
-        Input data to median function
+        Sorted input data to median function
     result : Array or MaskedArray
-        Result of median function
+        Result of median function.
     axis : int
         Axis along which the median was computed.
-    out : ndarray, optional
-        Output array in which to place the result.
 
     Returns
     -------
-    median : scalar or ndarray
-        Median or NaN in axes which contained NaN in the input.
+    result : scalar or ndarray
+        Median or NaN in axes which contained NaN in the input.  If the input
+        was an array, NaN will be inserted in-place.  If a scalar, either the
+        input itself or a scalar NaN.
     """
     if data.size == 0:
         return result
     n = np.isnan(data.take(-1, axis=axis))
     # masked NaN values are ok
     if np.ma.isMaskedArray(n):
         n = n.filled(False)
-    if result.ndim == 0:
-        if n == True:
-            if out is not None:
-                out[...] = data.dtype.type(np.nan)
-                result = out
-            else:
-                result = data.dtype.type(np.nan)
-    elif np.count_nonzero(n.ravel()) > 0:
+    if np.count_nonzero(n.ravel()) > 0:
+        # Without given output, it is possible that the current result is a
+        # numpy scalar, which is not writeable.  If so, just return nan.
+        if isinstance(result, np.generic):
+            return data.dtype.type(np.nan)
+
         result[n] = np.nan
     return result
 
```

### `numpy/ma/extras.py`
```diff
@@ -750,7 +750,7 @@ def _median(a, axis=None, out=None, overwrite_input=False):
             s = mid.sum(out=out)
             if not odd:
                 s = np.true_divide(s, 2., casting='safe', out=out)
-            s = np.lib.utils._median_nancheck(asorted, s, axis, out)
+            s = np.lib.utils._median_nancheck(asorted, s, axis)
         else:
             s = mid.mean(out=out)
 
@@ -790,7 +790,7 @@ def replace_masked(s):
         s = np.ma.sum(low_high, axis=axis, out=out)
         np.true_divide(s.data, 2., casting='unsafe', out=s.data)
 
-        s = np.lib.utils._median_nancheck(asorted, s, axis, out)
+        s = np.lib.utils._median_nancheck(asorted, s, axis)
     else:
         s = np.ma.mean(low_high, axis=axis, out=out)
 
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `numpy/lib/function_base.py`
- `numpy/lib/utils.py`
- `numpy/ma/extras.py`
