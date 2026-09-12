# Reference solution — GH895_gpytorch_1919

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH895_gpytorch_1919`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH895_gpytorch_1919/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `gpytorch/kernels/periodic_kernel.py` (modified, +57/-40)
- `test/kernels/test_periodic_kernel.py` (modified, +8/-1)

## Diff Summary (What the Fix Changes)

### `gpytorch/kernels/periodic_kernel.py`
```diff
@@ -17,9 +17,9 @@ class PeriodicKernel(Kernel):
     .. math::
 
         \begin{equation*}
-            k_{\text{Periodic}}(\mathbf{x_1}, \mathbf{x_2}) = \exp \left(
+            k_{\text{Periodic}}(\mathbf{x}, \mathbf{x'}) = \exp \left(
             -2 \sum_i
-            \frac{\sin ^2 \left( \frac{\pi}{p} (\mathbf{x_{1,i}} - \mathbf{x_{2,i}} ) \right)}{\lambda}
+            \frac{\sin ^2 \left( \frac{\pi}{p} ({x_{i}} - {x_{i}'} ) \right)}{\lambda}
             \right)
         \end{equation*}
 
@@ -28,44 +28,44 @@ class PeriodicKernel(Kernel):
     * :math:`p` is the period length parameter.
     * :math:`\lambda` is a lengthscale parameter.
 
-    Equation is based on [David Mackay's Introduction to Gaussian Processes equation 47]
-    (http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.81.1927&rep=rep1&type=pdf)
-    albeit without feature-specific lengthscales and period lengths. The exponential
+    Equation is based on `David Mackay's Introduction to Gaussian Processes equation 47`_
+    (albeit without feature-specific lengthscales and period lengths). The exponential
     coefficient was changed and lengthscale is not squared to maintain backwards compatibility
 
     .. note::
 
         This kernel does not have an `outputscale` parameter. To add a scaling parameter,
         decorate this kernel with a :class:`gpytorch.kernels.ScaleKernel`.
 
-    .. note::
-
-        This kernel does not have an ARD lengthscale or period length option.
-
-    Args:
-        :attr:`batch_shape` (torch.Size, optional):
-            Set this if you want a separate lengthscale for each
-             batch of input data. It should be `b` if :attr:`x1` is a `b x n x d` tensor. Default: `torch.Size([])`.
-        :attr:`active_dims` (tuple of ints, optional):
-            Set this if you want to compute the covariance of only a few input dimensions. The ints
-            corresponds to the indices of the dimensions. Default: `None`.
-        :attr:`period_length_prior` 
```

## Moved from `brief.md`

## Files That May Need Changes

- `gpytorch/kernels/periodic_kernel.py`
