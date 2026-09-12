# Reference solution — GH949_gpytorch_1446

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH949_gpytorch_1446`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH949_gpytorch_1446/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `gpytorch/kernels/rff_kernel.py` (modified, +2/-2)
- `gpytorch/lazy/low_rank_root_added_diag_lazy_tensor.py` (modified, +8/-2)
- `gpytorch/lazy/low_rank_root_lazy_tensor.py` (modified, +1/-1)
- `gpytorch/lazy/root_lazy_tensor.py` (modified, +7/-0)
- `gpytorch/test/lazy_tensor_test_case.py` (modified, +6/-1)
- `test/examples/test_sgpr_regression.py` (modified, +4/-0)
- `test/kernels/test_rff_kernel.py` (modified, +22/-0)
- `test/lazy/test_low_rank_root_added_diag_lazy_tensor.py` (added, +140/-0)
- `test/lazy/test_low_rank_root_lazy_tensor.py` (added, +42/-0)

## Diff Summary (What the Fix Changes)

### `gpytorch/kernels/rff_kernel.py`
```diff
@@ -6,7 +6,7 @@
 import torch
 from torch import Tensor
 
-from ..lazy import MatmulLazyTensor, RootLazyTensor
+from ..lazy import LowRankRootLazyTensor, MatmulLazyTensor
 from ..models.exact_prediction_strategies import RFFPredictionStrategy
 from .kernel import Kernel
 
@@ -128,7 +128,7 @@ def forward(self, x1: Tensor, x2: Tensor, diag: bool = False, last_dim_is_batch:
         if diag:
             return (z1 * z2).sum(-1) / D
         if x1_eq_x2:
-            return RootLazyTensor(z1 / math.sqrt(D))
+            return LowRankRootLazyTensor(z1 / math.sqrt(D))
         else:
             return MatmulLazyTensor(z1 / D, z2.transpose(-1, -2))
 
```

### `gpytorch/lazy/low_rank_root_added_diag_lazy_tensor.py`
```diff
@@ -8,6 +8,7 @@
 from .added_diag_lazy_tensor import AddedDiagLazyTensor
 from .diag_lazy_tensor import ConstantDiagLazyTensor, DiagLazyTensor
 from .low_rank_root_lazy_tensor import LowRankRootLazyTensor
+from .sum_batch_lazy_tensor import SumBatchLazyTensor
 
 
 class LowRankRootAddedDiagLazyTensor(AddedDiagLazyTensor):
@@ -49,6 +50,9 @@ def _solve(self, rhs, preconditioner=None, num_tridiag=0):
 
         return solve
 
+    def _sum_batch(self, dim):
+        return SumBatchLazyTensor(self, dim)
+
     def _logdet(self):
         chol_cap_mat = self.chol_cap_mat
         logdet_cap_mat = 2 * torch.diagonal(chol_cap_mat, offset=0, dim1=-2, dim2=-1).log().sum(-1)
@@ -63,7 +67,7 @@ def __add__(self, other):
         if isinstance(other, DiagLazyTensor):
             return self.__class__(self._lazy_tensor, self._diag_tensor + other)
         else:
-            return self.__class__(self._lazy_tensor + other, self._diag_tensor)
+            return AddedDiagLazyTensor(self._lazy_tensor + other, self._diag_tensor)
 
     def inv_quad_logdet(self, inv_quad_rhs=None, logdet=False, reduce_inv_quad=True):
         if not self.is_square:
@@ -96,7 +100,9 @@ def inv_quad_logdet(self, inv_quad_rhs=None, logdet=False, reduce_inv_quad=True)
 
         if inv_quad_rhs is not None:
             self_inv_rhs = self._solve(inv_quad_rhs)
-            inv_quad_term = inv_quad_rhs.transpose(-2, -1).matmul(self_inv_rhs)
+            inv_quad_term = (inv_quad_rhs * self_inv_rhs).sum(dim=-2)
+            if reduce_inv_quad:
+                inv_quad_term = inv_quad_term.sum(dim=-1)
 
         if logdet:
             logdet_term = self._logdet()
```

### `gpytorch/lazy/low_rank_root_lazy_tensor.py`
```diff
@@ -49,4 +49,4 @@ def __add__(self, other):
         if isinstance(other, DiagLazyTensor):
             return LowRankRootAddedDiagLazyTensor(self, other)
         else:
-            return super().__add__(self, other)
+            return super().__add__(other)
```

### `gpytorch/lazy/root_lazy_tensor.py`
```diff
@@ -55,6 +55,13 @@ def _getitem(self, row_index, col_index, *batch_indices):
     def _matmul(self, rhs):
         return self.root._matmul(self.root._t_matmul(rhs))
 
+    def _mul_constant(self, constant):
+        if constant > 0:
+            res = self.__class__(self.root._mul_constant(constant.sqrt()))
+        else:
+            res = super()._mul_constant(constant)
+        return res
+
     def _t_matmul(self, rhs):
         # Matrix is symmetric
         return self._matmul(rhs)
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `gpytorch/kernels/rff_kernel.py`
- `gpytorch/lazy/low_rank_root_added_diag_lazy_tensor.py`
- `gpytorch/lazy/low_rank_root_lazy_tensor.py`
- `gpytorch/lazy/root_lazy_tensor.py`
