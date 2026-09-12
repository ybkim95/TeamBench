# Reference solution — GH970_gpytorch_1312

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH970_gpytorch_1312`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH970_gpytorch_1312/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `gpytorch/distributions/multitask_multivariate_normal.py` (modified, +20/-0)
- `test/distributions/test_multitask_multivariate_normal.py` (modified, +19/-0)

## Diff Summary (What the Fix Changes)

### `gpytorch/distributions/multitask_multivariate_normal.py`
```diff
@@ -3,6 +3,7 @@
 import torch
 
 from ..lazy import BlockDiagLazyTensor, BlockInterleavedLazyTensor, CatLazyTensor, LazyTensor, lazify
+from ..utils.broadcasting import _mul_broadcast_shape
 from .multivariate_normal import MultivariateNormal
 
 
@@ -33,6 +34,25 @@ def __init__(self, mean, covariance_matrix, validate_args=False, interleaved=Tru
         if mean.dim() < 2:
             raise RuntimeError("mean should be a matrix or a batch matrix (batch mode)")
 
+        # Ensure that shapes are broadcasted appropriately across the mean and covariance
+        # Means can have singleton dimensions for either the `n` or `t` dimensions
+        batch_shape = _mul_broadcast_shape(mean.shape[:-2], covariance_matrix.shape[:-2])
+        if mean.shape[-2:].numel() != covariance_matrix.size(-1):
+            if covariance_matrix.size(-1) % mean.shape[-2:].numel():
+                raise RuntimeError(
+                    f"mean shape {mean.shape} is incompatible with covariance shape {covariance_matrix.shape}"
+                )
+            elif mean.size(-2) == 1:
+                mean = mean.expand(*batch_shape, covariance_matrix.size(-1) // mean.size(-1), mean.size(-1))
+            elif mean.size(-1) == 1:
+                mean = mean.expand(*batch_shape, mean.size(-2), covariance_matrix.size(-2) // mean.size(-2))
+            else:
+                raise RuntimeError(
+                    f"mean shape {mean.shape} is incompatible with covariance shape {covariance_matrix.shape}"
+                )
+        else:
+            mean = mean.expand(*batch_shape, *mean.shape[-2:])
+
         self._output_shape = mean.shape
         # TODO: Instead of transpose / view operations, use a PermutationLazyTensor (see #539) to handle interleaving
         self._interleaved = interleaved
```

## Moved from `brief.md`

## Files That May Need Changes

- `gpytorch/distributions/multitask_multivariate_normal.py`
