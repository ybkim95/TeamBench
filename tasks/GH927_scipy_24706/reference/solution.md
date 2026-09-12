# Reference solution — GH927_scipy_24706

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH927_scipy_24706`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH927_scipy_24706/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `scipy/sparse/csgraph/_validation.py` (modified, +8/-3)
- `scipy/sparse/csgraph/tests/test_connected_components.py` (modified, +33/-2)

## Diff Summary (What the Fix Changes)

### `scipy/sparse/csgraph/_validation.py`
```diff
@@ -32,13 +32,18 @@ def validate_graph(csgraph, directed, dtype=DTYPE,
 
     if issparse(csgraph):
         if csr_output:
-            csgraph = csgraph.tocsr(copy=copy_if_sparse).astype(DTYPE, copy=False)
+            if csgraph.format == "bsr":
+                csgraph = csgraph.tocsr(copy=copy_if_sparse)
+                csgraph.eliminate_zeros()
+                csgraph = csgraph.astype(dtype, copy=False)
+            else:
+                csgraph = csgraph.tocsr(copy=copy_if_sparse).astype(dtype, copy=False)
         else:
             csgraph = csgraph_to_dense(csgraph, null_value=null_value_out)
     elif np.ma.isMaskedArray(csgraph):
         if dense_output:
             mask = csgraph.mask
-            csgraph = np.array(csgraph.data, dtype=DTYPE, copy=copy_if_dense)
+            csgraph = np.array(csgraph.data, dtype=dtype, copy=copy_if_dense)
             csgraph[mask] = null_value_out
         else:
             csgraph = csgraph_from_masked(csgraph)
@@ -50,7 +55,7 @@ def validate_graph(csgraph, directed, dtype=DTYPE,
                                                 nan_null=nan_null,
                                                 infinity_null=infinity_null)
             mask = csgraph.mask
-            csgraph = np.asarray(csgraph.data, dtype=DTYPE)
+            csgraph = np.asarray(csgraph.data, dtype=dtype)
             csgraph[mask] = null_value_out
         else:
             csgraph = csgraph_from_dense(csgraph, null_value=null_value_in,
```

## Moved from `brief.md`

## Files That May Need Changes

- `scipy/sparse/csgraph/_validation.py`
