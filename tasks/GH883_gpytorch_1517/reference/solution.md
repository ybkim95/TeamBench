# Reference solution — GH883_gpytorch_1517

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH883_gpytorch_1517`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH883_gpytorch_1517/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `gpytorch/models/exact_prediction_strategies.py` (modified, +16/-9)
- `test/examples/test_sgpr_regression.py` (modified, +20/-40)

## Diff Summary (What the Fix Changes)

### `gpytorch/models/exact_prediction_strategies.py`
```diff
@@ -667,19 +667,24 @@ class SGPRPredictionStrategy(DefaultPredictionStrategy):
     def covar_cache(self):
         # Here, the covar_cache is going to be the inverse of K_{XX} + \sigma^2 I
         # This is easily computed using Woodbury
+        # K_{XX} + \sigma^2 I = R R^T + \sigma^2 I
+        #                     = \sigma^{-2} ( I - \sigma^{-2} R (I + \sigma^{-2} R^T R)^{-1} R^T  )
         train_train_covar = self.lik_train_train_covar.evaluate_kernel()
 
         # Get terms needed for woodbury
-        root = train_train_covar._lazy_tensor.root_decomposition().root
-        inv_diag = train_train_covar._diag_tensor.inverse()
+        root = train_train_covar._lazy_tensor.root_decomposition().root.evaluate()  # R
+        inv_diag = train_train_covar._diag_tensor.inverse()  # \sigma^{-2}
 
         # Form LT using woodbury
-        ones = torch.tensor(1.0, dtype=inv_diag.dtype, device=inv_diag.device)
-        chol_factor = (root.transpose(-1, -2) @ root).add_diag(ones).cholesky().evaluate()
-        woodbury_term = torch.triangular_solve(
-            inv_diag.diag().unsqueeze(-2) * root.evaluate().transpose(-1, -2), chol_factor, upper=False
-        )[0]
-        inverse = AddedDiagLazyTensor(MatmulLazyTensor(woodbury_term.transpose(-1, -2), -woodbury_term), inv_diag)
+        ones = torch.tensor(1.0, dtype=root.dtype, device=root.device)
+        chol_factor = lazify(root.transpose(-1, -2) @ (inv_diag @ root)).add_diag(ones)  # (I + \sigma^{-2} R^T R)^{-1}
+        woodbury_term = inv_diag @ torch.triangular_solve(
+            root.transpose(-1, -2), chol_factor.cholesky().evaluate(), upper=False
+        )[0].transpose(-1, -2)
+        # woodbury_term @ woodbury_term^T = \sigma^{-2} R (I + \sigma^{-2} R^T R)^{-1} R^T \sigma^{-2}
+
+        inverse = AddedDiagLazyTensor(inv_diag, MatmulLazyTensor(-woodbury_term, woodbury_term.transpose(-1, -2)))
+        # \sigma^{-2} ( I - \sigma^{-2} R (I + \sigma^{-2} R^T R)^{-1} R^T  )
         return inverse
 
   
```

## Moved from `brief.md`

## Files That May Need Changes

- `gpytorch/models/exact_prediction_strategies.py`
