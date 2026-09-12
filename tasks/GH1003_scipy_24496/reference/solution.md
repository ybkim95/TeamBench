# Reference solution — GH1003_scipy_24496

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1003_scipy_24496`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1003_scipy_24496/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `scipy/sparse/_base.py` (modified, +7/-0)
- `scipy/sparse/_compressed.py` (modified, +9/-6)
- `scipy/sparse/_dia.py` (modified, +4/-3)
- `scipy/sparse/tests/test_base.py` (modified, +57/-0)

## Diff Summary (What the Fix Changes)

### `scipy/sparse/_base.py`
```diff
@@ -1417,6 +1417,13 @@ def sum(self, axis=None, dtype=None, out=None):
         # Mimic numpy's casting.
         res_dtype = get_sum_dtype(self.dtype)
 
+        if dtype is not None:
+            # Before casting to the requested dtype, canonicalize duplicates and zeros.
+            if hasattr(self, 'sum_duplicates'):
+                self.sum_duplicates()
+            temp = self.astype(dtype, copy=False).sum(axis=axis, dtype=None, out=out)
+            return temp.astype(dtype, copy=False)
+
         # Note: all valid 1D axis values are canonically `None`.
         if axis is None:
             if self.nnz == 0:
```

### `scipy/sparse/_compressed.py`
```diff
@@ -498,16 +498,19 @@ def sum(self, axis=None, dtype=None, out=None):
         if (self.ndim == 2 and not hasattr(self, 'blocksize') and
                 axis in self._swap(((1, -1), (0, -2)))[0]):
             # faster than multiplication for large minor axis in CSC/CSR
-            res_dtype = get_sum_dtype(self.dtype)
-            ret = np.zeros(len(self.indptr) - 1, dtype=res_dtype)
-
-            major_index, value = self._minor_reduce(np.add)
+            
+            res_dtype = get_sum_dtype(self.dtype) if dtype is None else dtype
+            self_to_reduce = self.astype(res_dtype, copy=False)
+            
+            # Fast path: reduce along minor axis
+            ret = np.zeros(len(self_to_reduce.indptr) - 1, dtype=res_dtype)
+            major_index, value = self_to_reduce._minor_reduce(np.add)
             ret[major_index] = value
-            ret = self._ascontainer(ret)
+            ret = self_to_reduce._ascontainer(ret)
             if axis % 2 == 1:
                 ret = ret.T
 
-            return ret.sum(axis=(), dtype=dtype, out=out)
+            return ret.sum(axis=(), dtype=res_dtype, out=out)
         else:
             return _spbase.sum(self, axis=axis, dtype=dtype, out=out)
 
```

### `scipy/sparse/_dia.py`
```diff
@@ -142,13 +142,13 @@ def _getnnz(self, axis=None):
     def sum(self, axis=None, dtype=None, out=None):
         axis = validateaxis(axis)
 
-        res_dtype = get_sum_dtype(self.dtype)
+        res_dtype = dtype if dtype is not None else get_sum_dtype(self.dtype)
         num_rows, num_cols = self.shape
         ret = None
 
         if axis == (0,):
             mask = self._data_mask()
-            x = (self.data * mask).sum(axis=0)
+            x = (self.data * mask).sum(dtype=res_dtype, axis=0)
             if x.shape[0] == num_cols:
                 res = x
             else:
@@ -160,7 +160,8 @@ def sum(self, axis=None, dtype=None, out=None):
             row_sums = np.zeros((num_rows, 1), dtype=res_dtype)
             one = np.ones(num_cols, dtype=res_dtype)
             dia_matvec(num_rows, num_cols, len(self.offsets),
-                       self.data.shape[1], self.offsets, self.data, one, row_sums)
+                       self.data.shape[1], self.offsets, 
+                       self.data.astype(res_dtype), one, row_sums)
 
             row_sums = self._ascontainer(row_sums)
 
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `scipy/sparse/_base.py`
- `scipy/sparse/_compressed.py`
- `scipy/sparse/_dia.py`
