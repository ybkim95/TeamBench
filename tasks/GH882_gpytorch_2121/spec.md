# GH882_gpytorch_2121: Fix multitask/added_loss_term bugs in SGPR regression — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/cornellius-gp/gpytorch/issues/2113
- Repo: https://github.com/cornellius-gp/gpytorch

## Issue Description

# 🐛 Bug

<!-- A clear and concise description of what the bug is. -->
In implementing multitask sparse Gaussian processes, I got the index error message "tuple index out of range" in calculating loss using mll function. 
## To reproduce

** Code snippet to reproduce **
```python
import math
import torch
import gpytorch

train_x = torch.linspace(0, 1, 100)

train_y = torch.stack([
    torch.sin(train_x * (2 * math.pi)) + torch.randn(train_x.size()) * 0.2,
    torch.cos(train_x * (2 * math.pi)) + torch.randn(train_x.size()) * 0.2,
], -1)

class MultitaskGPModel(gpytorch.models.ExactGP):
    def __init__(self, train_x, train_y, likelihood):
        super(MultitaskGPModel, self).__init__(train_x, train_y, likelihood)
        self.mean_module = gpytorch.means.MultitaskMean(gpytorch.means.ConstantMean(), num_tasks=2)
        self.covar_module = gpytorch.kernels.MultitaskKernel(gpytorch.kernels.InducingPointKernel(gpytorch.kernels.LinearKernel(), inducing_points=train_x[range(0,100,10)], likelihood=likelihood), num_tasks=2, rank=1)

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultitaskMultivariateNormal(mean_x, covar_x)


likelihood = gpytorch.likelihoods.MultitaskGaussianLikelihood(num_tasks=2)
model = MultitaskGPModel(train_x, train_y, likelihood)

model.train()
likelihood.train()

optimizer = torch.optim.Adam(model.parameters(), lr=0.1)  # Includes GaussianLikelihood parameters

mll = gpytorch.mlls.ExactMarginalLogLikelihood(likelihood, model)

optimizer.zero_grad()
output = model(train_x)
loss = -mll(output, train_y)
```

** Stack trace/error message **
```
Traceback (most recent call last):

  File "C:\code.py", line 36, in <module>
    loss = -mll(output, train_y)

  File "C:\...\anaconda3\lib\site-packages\gpytorch\module.py", line 30, in __call__
    outputs = self.forward(*inputs, **kwargs)

  File "C:\...\anaconda3\lib\site-packages\gpytorch\mlls\exact_marginal_log_likelihood.py", line 63, in forward
    res = self._add_other_terms(res, params)

  File "C:\...\anaconda3\lib\site-packages\gpytorch\mlls\exact_marginal_log_likelihood.py", line 39, in _add_other_terms
    res = res.add(added_loss_term.loss(*params))

  File "C:\...\anaconda3\lib\site-packages\gpytorch\mlls\inducing_point_kernel_added_loss_term.py", line 17, in loss
    noise_diag = self.likelihood._shaped_noise_covar(shape, *params).diag()

  File "C:\...\anaconda3\lib\site-packages\gpytorch\likelihoods\multitask_gaussian_likelihood.py", line 117, in _shaped_noise_covar
    eye_lt = ConstantDiagLazyTensor(torch.ones(*shape[:-2], 1, dtype=dtype, device=device), diag_shape=shape[-2])

IndexError: tuple index out of range
```

## Expected Behavior

<!-- A clear and concise description of what you expected to happen. -->
It should calculate loss.
## System information

**Please complete the following information:**
GPyTorch 1.7.0
PyTorch 1.12.0
Windows 10

## Additional context
Add any other context about the problem here.

## PR Review Comments

**[user]** on `test/examples/test_kronecker_multitask_sgpr_regression.py`:

Orthogonal to this PR: It seems like this could be generally useful and we may want to factor it out into sth like a `GPyTorchTestCase`?

**[user]** on `test/examples/test_kronecker_multitask_sgpr_regression.py`:

I think this functionality is already in [BaseTestCase](https://github.com/cornellius-gp/gpytorch/blob/master/gpytorch/test/base_test_case.py), so we probably should be using it 😅

**[user]** on `test/examples/test_kronecker_multitask_sgpr_regression.py`:

I substituted "inducing_point_kernel_added_loss_term.py" in "gpytorch/mlls" with this revised file here and run the code snippet that I submitted in GitHub (#2113). But it didn't work. Did I do something wrong or is the issue not solved yet?

**[user]** on `test/examples/test_kronecker_multitask_sgpr_regression.py`:

[user] this PR is being merged in today. If you are still experiencing issues, please open up another issue, rather than commenting on this PR. Please also provide more information than "But it didn't work."

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
