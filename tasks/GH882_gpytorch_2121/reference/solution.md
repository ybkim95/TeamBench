# Reference solution — GH882_gpytorch_2121

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH882_gpytorch_2121`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH882_gpytorch_2121/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/source/marginal_log_likelihoods.rst` (modified, +20/-0)
- `gpytorch/mlls/added_loss_term.py` (modified, +69/-2)
- `gpytorch/mlls/inducing_point_kernel_added_loss_term.py` (modified, +41/-3)
- `gpytorch/mlls/kl_gaussian_added_loss_term.py` (modified, +18/-1)
- `test/examples/test_kronecker_multitask_sgpr_regression.py` (added, +86/-0)
- `test/mlls/test_inducing_point_kernel_added_loss_term.py` (added, +45/-0)

## Diff Summary (What the Fix Changes)

### `gpytorch/mlls/added_loss_term.py`
```diff
@@ -1,6 +1,73 @@
 #!/usr/bin/env python3
 
+from abc import ABC, abstractmethod
 
-class AddedLossTerm(object):
-    def loss(self):
+from torch import Tensor
+
+
+class AddedLossTerm(ABC):
+    r"""
+    AddedLossTerms are registered onto GPyTorch models (or their children `gpytorch.Modules`).
+
+    If a model (or any of its children modules) has an added loss term, then
+    all optimization objective functions (e.g. :class:`~gpytorch.mlls.ExactMarginalLogLikelihood`,
+    :class:`~gpytorch.mlls.VariationalELBO`, etc.) will be ammended to include an additive term
+    defined by the :meth:`~gpytorch.mlls.AddedLossTerm.loss` method.
+
+    As an example, consider the following toy AddedLossTerm that adds a random number to any objective function:
+
+    .. code-block:: python
+
+        class RandomNumberAddedLoss
+            # Adds a random number ot the loss
+            def __init__(self, dtype, device):
+                self.dtype, self.device = dtype, device
+
+            def loss(self):
+                # This dynamically defines the added loss term
+                return torch.randn(torch.Size([]), dtype=self.dtype, device=self.device)
+
+        class MyExactGP(gpytorch.ExactGP):
+            def __init__(self, train_x, train_y):
+                super().__init__(train_x, train_y, gpytorch.likelihood.GaussianLikelihood())
+                self.mean_module = gpytorch.means.ZeroMean()
+                self.covar_module = gpytorch.kernels.RBFKernel()
+
+                # Create the added loss term
+                self.register_added_loss_term("random_added_loss")
+
+            def forward(self, x):
+                # Update loss term
+                new_added_loss_term = RandomNumberAddedLoss(dtype=x.dtype, device=x.device)
+                self.update_added_loss_term("random_added_loss", new_added_loss_term)
+
+                # Run the remainder of the forward method
+                return gpytorch.distribution.MultivariateNormal(self.mean_module(x),
```

### `gpytorch/mlls/inducing_point_kernel_added_loss_term.py`
```diff
@@ -1,18 +1,56 @@
 #!/usr/bin/env python3
 
+import torch
+
+from ..distributions import MultivariateNormal
+from ..likelihoods import GaussianLikelihood, MultitaskGaussianLikelihood
 from .added_loss_term import AddedLossTerm
 
 
 class InducingPointKernelAddedLossTerm(AddedLossTerm):
-    def __init__(self, prior_dist, variational_dist, likelihood):
+    r"""
+    An added loss term that computes the additional "regularization trace term" of the SGPR objective function.
+
+    .. math::
+        -\frac{1}{2 \sigma^2} \text{Tr} \left( \mathbf K_{\mathbf X \mathbf X} - \mathbf Q \right)
+
+
+    where :math:`\mathbf Q = \mathbf K_{\mathbf X \mathbf Z} \mathbf K_{\mathbf Z \mathbf Z}^{-1}
+    \mathbf K_{\mathbf Z \mathbf X}` is the Nystrom approximation of :math:`\mathbf K_{\mathbf X \mathbf X}`
+    given by inducing points :math:`\mathbf Z`, and :math:`\sigma^2` is the observational noise
+    of the Gaussian likelihood.
+
+    See `Titsias, 2009`_, Eq. 9 for more more information.
+
+    :param prior_dist: A multivariate normal :math:`\mathcal N ( \mathbf 0, \mathbf K_{\mathbf X \mathbf X} )`
+        with covariance matrix :math:`\mathbf K_{\mathbf X \mathbf X}`.
+    :param variational_dist: A multivariate normal :math:`\mathcal N ( \mathbf 0, \mathbf Q`
+        with covariance matrix :math:`\mathbf Q = \mathbf K_{\mathbf X \mathbf Z}
+        \mathbf K_{\mathbf Z \mathbf Z}^{-1} \mathbf K_{\mathbf Z \mathbf X}`.
+    :param likelihood: The Gaussian likelihood with observational noise :math:`\sigma^2`.
+
+    .. _Titsias, 2009:
+        https://arxiv.org/pdf/1302.4245.pdf
+    """
+
+    def __init__(
+        self, prior_dist: MultivariateNormal, variational_dist: MultivariateNormal, likelihood: GaussianLikelihood
+    ):
         self.prior_dist = prior_dist
         self.variational_dist = variational_dist
         self.likelihood = likelihood
 
-    def loss(self, *params):
+    def loss(self, *params) -> torch.Tensor:
         prior_covar = self.prior_dis
```

### `gpytorch/mlls/kl_gaussian_added_loss_term.py`
```diff
@@ -2,11 +2,28 @@
 
 from torch.distributions import kl_divergence
 
+from ..distributions import MultivariateNormal
 from .added_loss_term import AddedLossTerm
 
 
 class KLGaussianAddedLossTerm(AddedLossTerm):
-    def __init__(self, q_x, p_x, n, data_dim):
+    r"""
+    This class is used by variational GPLVM models.
+    It adds the KL divergence between two multivariate Gaussian distributions:
+    scaled by the size of the data and the number of output dimensions.
+
+    .. math::
+
+        D_\text{KL} \left( q(\mathbf x) \Vert p(\mathbf x) \right)
+
+
+    :param q_x: The MVN distribution :math:`q(\mathbf x)`.
+    :param p_x: The MVN distribution :math:`p(\mathbf x)`.
+    :param n: Size of the latent space.
+    :param data_dim: Dimensionality of the :math:`\mathbf Y` values.
+    """
+
+    def __init__(self, q_x: MultivariateNormal, p_x: MultivariateNormal, n: int, data_dim: int):
         super().__init__()
         self.q_x = q_x
         self.p_x = p_x
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `gpytorch/mlls/added_loss_term.py`
- `gpytorch/mlls/inducing_point_kernel_added_loss_term.py`
- `gpytorch/mlls/kl_gaussian_added_loss_term.py`
