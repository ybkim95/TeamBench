# Reference solution — GH896_gpytorch_1299

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH896_gpytorch_1299`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH896_gpytorch_1299/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `gpytorch/lazy/added_diag_lazy_tensor.py` (modified, +25/-1)
- `test/examples/test_white_noise_regression.py` (modified, +5/-38)

## Diff Summary (What the Fix Changes)

### `gpytorch/lazy/added_diag_lazy_tensor.py`
```diff
@@ -68,12 +68,33 @@ def __add__(self, other):
             return AddedDiagLazyTensor(self._lazy_tensor + other, self._diag_tensor)
 
     def _preconditioner(self):
+        r"""
+        Here we use a partial pivoted Cholesky preconditioner:
+
+        K \approx L L^T + D
+
+        where L L^T is a low rank approximation, and D is a diagonal.
+        We can compute the preconditioner's inverse using Woodbury
+
+        (L L^T + D)^{-1} = D^{-1} - D^{-1} L (I + L D^{-1} L^T)^{-1} L^T D^{-1}
+
+        This function returns:
+        - A function `precondition_closure` that computes the solve (L L^T + D)^{-1} x
+        - A LazyTensor `precondition_lt` that represents (L L^T + D)
+        - The log determinant of (L L^T + D)
+        """
+
         if self.preconditioner_override is not None:
             return self.preconditioner_override(self)
 
         if settings.max_preconditioner_size.value() == 0 or self.size(-1) < settings.min_preconditioning_size.value():
             return None, None, None
 
+        # Cache a QR decomposition [Q; Q'] R = [D^{-1/2}; L]
+        # This makes it fast to compute solves and log determinants with it
+        #
+        # Through woodbury, (L L^T + D)^{-1} reduces down to (D^{-1} - D^{-1/2} Q Q^T D^{-1/2})
+        # Through matrix determinant lemma, log |L L^T + D| reduces down to 2 log |R|
         if self._q_cache is None:
             max_iter = settings.max_preconditioner_size.value()
             self._piv_chol_self = pivoted_cholesky.pivoted_cholesky(self._lazy_tensor, max_iter)
@@ -87,6 +108,7 @@ def _preconditioner(self):
 
         # NOTE: We cannot memoize this precondition closure as it causes a memory leak
         def precondition_closure(tensor):
+            # This makes it fast to compute solves with it
             qqt = self._q_cache.matmul(self._q_cache.transpose(-2, -1).matmul(tensor))
             if self._constant_diag:
                 return (1 / self._noise) * (tensor - qqt)
@@ -102,6 +124,7 @@ def
```

## Moved from `brief.md`

## Files That May Need Changes

- `gpytorch/lazy/added_diag_lazy_tensor.py`
