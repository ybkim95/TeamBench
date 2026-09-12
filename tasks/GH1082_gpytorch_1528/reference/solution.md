# Reference solution — GH1082_gpytorch_1528

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1082_gpytorch_1528`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1082_gpytorch_1528/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `gpytorch/kernels/inducing_point_kernel.py` (modified, +2/-0)
- `gpytorch/models/exact_prediction_strategies.py` (modified, +32/-6)
- `test/examples/test_sgpr_regression.py` (modified, +16/-0)

## Diff Summary (What the Fix Changes)

### `gpytorch/kernels/inducing_point_kernel.py`
```diff
@@ -28,6 +28,8 @@ def __init__(self, base_kernel, inducing_points, likelihood, active_dims=None):
     def _clear_cache(self):
         if hasattr(self, "_cached_kernel_mat"):
             del self._cached_kernel_mat
+        if hasattr(self, "_cached_kernel_inv_root"):
+            del self._cached_kernel_inv_root
 
     @property
     def _inducing_mat(self):
```

### `gpytorch/models/exact_prediction_strategies.py`
```diff
@@ -607,7 +607,7 @@ class SGPRPredictionStrategy(DefaultPredictionStrategy):
     @property
     @cached(name="covar_cache")
     def covar_cache(self):
-        # Here, the covar_cache is going to be the inverse of K_{XX} + \sigma^2 I
+        # Here, the covar_cache is going to be K_{UU}^{-1/2} K_{UX}( K_{XX} + \sigma^2 I )^{-1} K_{XU} K_{UU}^{-1/2}
         # This is easily computed using Woodbury
         # K_{XX} + \sigma^2 I = R R^T + \sigma^2 I
         #                     = \sigma^{-2} ( I - \sigma^{-2} R (I + \sigma^{-2} R^T R)^{-1} R^T  )
@@ -627,17 +627,33 @@ def covar_cache(self):
 
         inverse = AddedDiagLazyTensor(inv_diag, MatmulLazyTensor(-woodbury_term, woodbury_term.transpose(-1, -2)))
         # \sigma^{-2} ( I - \sigma^{-2} R (I + \sigma^{-2} R^T R)^{-1} R^T  )
-        return inverse
+
+        return root.transpose(-1, -2) @ (inverse @ root)
 
     def get_fantasy_strategy(self, inputs, targets, full_inputs, full_targets, full_output, **kwargs):
         raise NotImplementedError(
             "Fantasy observation updates not yet supported for models using SGPRPredictionStrategy"
         )
 
     def exact_prediction(self, joint_mean, joint_covar):
+        from ..kernels.inducing_point_kernel import InducingPointKernel
+
         # Find the components of the distribution that contain test data
         test_mean = joint_mean[..., self.num_train :]
-        test_test_covar = joint_covar[..., self.num_train :, self.num_train :].evaluate_kernel()
+
+        # If we're in lazy evaluation mode, let's use the base kernel of the SGPR output to compute the prior covar
+        test_test_covar = joint_covar[..., self.num_train :, self.num_train :]
+        if isinstance(test_test_covar, LazyEvaluatedKernelTensor) and isinstance(
+            test_test_covar.kernel, InducingPointKernel
+        ):
+            test_test_covar = LazyEvaluatedKernelTensor(
+                test_test_covar.x1,
+                test_test_covar.x2,
+                t
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `gpytorch/kernels/inducing_point_kernel.py`
- `gpytorch/models/exact_prediction_strategies.py`
