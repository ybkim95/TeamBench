# GH896_gpytorch_1299: Fix bug in fixed-noise preconditioner — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/cornellius-gp/gpytorch/issues/1298
- Repo: https://github.com/cornellius-gp/gpytorch

## Issue Description

# 🐛 Bug

Batched fixed noise GPs fail when the preconditioning threshold is reached. The concatenation in this line fails with a shape error.

https://github.com/cornellius-gp/gpytorch/blob/master/gpytorch/lazy/added_diag_lazy_tensor.py#L126

## To reproduce

** Code snippet to reproduce **
```python
import torch
import gpytorch

class BatchFixedNoiseGP(gpytorch.models.GP):
    def __init__(self, init_x, init_y, noise, batch_shape):
        super().__init__()
        self.mean_module = gpytorch.means.ZeroMean()
        self.covar_module = gpytorch.kernels.RBFKernel(batch_shape=batch_shape)
        self.likelihood = gpytorch.likelihoods.FixedNoiseGaussianLikelihood(noise)
        
    def forward(self, inputs):
        mean = self.mean_module(inputs)
        covar = self.covar_module(inputs)
        return gpytorch.distributions.MultivariateNormal(mean, covar)

batch_shape = [2]
train_x = torch.randn(*batch_shape, 101, 3)
train_y = torch.randn(*batch_shape, 101)
train_noise = torch.rand(*batch_shape, 101)

gp = BatchFixedNoiseGP(train_x, train_y, train_noise, batch_shape)
mll = gpytorch.mlls.ExactMarginalLogLikelihood(gp.likelihood, gp)

with gpytorch.settings.max_cholesky_size(100), gpytorch.settings.min_preconditioning_size(100):
    train_dist = gp(train_x)
    loss = -mll(train_dist, train_y).sum()
```

** Stack trace/error message **
```
RuntimeError                              Traceback (most recent call last)
<ipython-input-4-9e151e2de37a> in <module>
     24 with gpytorch.settings.max_cholesky_size(100), gpytorch.settings.min_preconditioning_size(100):
     25     train_dist = gp(train_x)
---> 26     loss = -mll(train_dist, train_y).sum()

~/Code/gpytorch/gpytorch/module.py in __call__(self, *inputs, **kwargs)
     26 
     27     def __call__(self, *inputs, **kwargs):
---> 28         outputs = self.forward(*inputs, **kwargs)
     29         if isinstance(outputs, list):
     30             return [_validate_module_outputs(output) for output in outputs]

~/Code/gpytorch/gpytorch/mlls/exact_marginal_log_likelihood.py in forward(self, function_dist, target, *params)
     49         # Get the log prob of the marginal distribution
     50         output = self.likelihood(function_dist, *params)
---> 51         res = output.log_prob(target)
     52 
     53         # Add additional terms (SGPR / learned inducing points, heteroskedastic likelihood models)

~/Code/gpytorch/gpytorch/distributions/multivariate_normal.py in log_prob(self, value)
    138 
    139         # Get log determininat and first part of quadratic form
--> 140         inv_quad, logdet = covar.inv_quad_logdet(inv_quad_rhs=diff.unsqueeze(-1), logdet=True)
    141 
    142         res = -0.5 * sum([inv_quad, logdet, diff.size(-1) * math.log(2 * math.pi)])

~/Code/gpytorch/gpytorch/lazy/lazy_tensor.py in inv_quad_logdet(self, inv_quad_rhs, logdet, reduce_inv_quad)
   1069             probe_vectors,
   1070             probe_vector_norms,
-> 1071             *args,
   1072         )
   1073 

~/Code/gpytorch/gpytorch/functions/_inv_quad_log_det.py in forward(ctx, representation_tree, dtype, device, matrix_shape, batch_shape, inv_quad, logdet, probe_vectors, probe_vector_norms, *args)
     65         lazy_tsr = ctx.representation_tree(*matrix_args)
     66         with torch.no_grad():
---> 67             preconditioner, precond_lt, logdet_correction = lazy_tsr._preconditioner()
     68 
     69         ctx.preconditioner = preconditioner

~/Code/gpytorch/gpytorch/lazy/added_diag_lazy_tensor.py in _preconditioner(self)
     84                 )
     85                 return None, None, None
---> 86             self._init_cache()
     87 
     88         # NOTE: We cannot memoize this precondition closure as it causes a memory leak

~/Code/gpytorch/gpytorch/lazy/added_diag_lazy_tensor.py in _init_cache(self)
    107             self._init_cache_for_constant_diag(eye, batch_shape, n, k)
    108         else:
--> 109             self._init_cache_for_non_constant_diag(eye, batch_shape, n)
    110 
    111         self._precond_lt = PsdSumLazyTensor(RootLazyTensor(self._piv_chol_self), self._diag_tensor)

~/Code/gpytorch/gpytorch/lazy/added_diag_lazy_tensor.py in _init_cache_for_non_constant_diag(self, eye, batch_shape, n)
    125         # With non-constant diagonals, we cant factor out the noise as easily
    126         # eye = eye.expand(*batch_shape, -1, -1)
--> 127         self._q_cache, self._r_cache = torch.qr(torch.cat((self._piv_chol_self / self._noise.sqrt(), eye)))
    128         self._q_cache = self._q_cache[..., :n, :] / self._noise.sqrt()
    129 

RuntimeError: Tensors must have same number of dimensions: got 3 and 2
```

## Expected Behavior

Everything works fine until the preconditioning threshold is reached. Obviously one would hope that it would continue to work.

## System information

**Please complete the following information:**
GPyTorch Version: 1.2.0
PyTorch Version:  '1.6.0.dev20200522'
OS: Ubuntu 16.04 LTS

## Additional context
This appears to fix the problem
```
    def _init_cache_for_non_constant_diag(self, eye, batch_shape, n):
        # With non-constant diagonals, we cant factor out the noise as easily
        eye = eye.expand(*batch_shape, -1, -1)
        self._q_cache, self._r_cache = torch.qr(torch.cat((self._piv_chol_self / self._noise.sqrt(), eye), dim=-2))
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Thanks for the catch. I'll take a look

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
