# GH910_gpytorch_2123: Fix bug with Multitask DeepGP predictive variances. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/cornellius-gp/gpytorch/issues/2702
- Repo: https://github.com/cornellius-gp/gpytorch

## Issue Description

# 🐛 Bug

In GPyTorch v1.15.1, even after fixing the problem with the missing `protein.mat` dataset, example "Exact GP Regression with Multiple GPUs" fails because multi-GPU support is apparently broken.

This problem first appeared in #2700 , but was mistaken by some incompatibility trying to combine multi-GPU training with exact regression on multiple classification labels.

Later, it was isolated in #2699 after fixing the missing `protein.mat` dataset in example "Exact GP Regression with Multiple GPUs", and still getting an error. I have created this new issue to tackle the problem with multi-GPU training, so that #2699 can be closed.

## To reproduce

** Code snippet to reproduce **

This code comes from this fork of ["Exact GP Regression with Multiple GPUs"](https://github.com/rcasero/gpytorch/blob/2699-bug-protein-dataset-url-does-not-exist/examples/02_Scalable_Exact_GPs/Simple_MultiGPU_GP_Regression.ipynb).

```python
import torch
import gpytorch
import sys
sys.path.append('../../../PyTorch-LBFGS/functions')
from LBFGS import FullBatchLBFGS

%matplotlib inline
%load_ext autoreload
%autoreload 2

import os
import urllib.request

import numpy as np
import pandas as pd

dataset = 'protein'
dataset_url = f'https://github.com/treforevans/uci_datasets/raw/refs/heads/master/uci_datasets/{dataset}/data.csv.gz'
dataset_filename = '../data.csv.gz'
if not os.path.isfile(dataset_filename):
    print(f'Downloading \'{dataset}\' UCI dataset...')
    urllib.request.urlretrieve(dataset_url, dataset_filename)

data = pd.read_csv(dataset_filename, header=None, usecols=[0, 1, 2], nrows=10_000).to_numpy(dtype=np.float32)
data = torch.tensor(data)

N = data.shape[0]
# make train/val/test
n_train = int(0.8 * N)
train_x, train_y = data[:n_train, :-1], data[:n_train, -1]
test_x, test_y = data[n_train:, :-1], data[n_train:, -1]

# normalize features
mean = train_x.mean(dim=-2, keepdim=True)
std = train_x.std(dim=-2, keepdim=True) + 1e-6 # prevent dividing by 0
train_x = (train_x - mean) / std
test_x = (test_x - mean) / std

# normalize labels
mean, std = train_y.mean(),train_y.std()
train_y = (train_y - mean) / std
test_y = (test_y - mean) / std

# make continguous
train_x, train_y = train_x.contiguous(), train_y.contiguous()
test_x, test_y = test_x.contiguous(), test_y.contiguous()

output_device = torch.device('cuda:0')

train_x, train_y = train_x.to(output_device), train_y.to(output_device)
test_x, test_y = test_x.to(output_device), test_y.to(output_device)

n_devices = torch.cuda.device_count()
print('Planning to run on {} GPUs.'.format(n_devices))

class ExactGPModel(gpytorch.models.ExactGP):
    def __init__(self, train_x, train_y, likelihood, n_devices):
        super(ExactGPModel, self).__init__(train_x, train_y, likelihood)
        self.mean_module = gpytorch.means.ConstantMean()
        base_covar_module = gpytorch.kernels.ScaleKernel(gpytorch.kernels.RBFKernel())
        
        self.covar_module = gpytorch.kernels.MultiDeviceKernel(
            base_covar_module, device_ids=range(n_devices),
            output_device=output_device
        )
    
    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)

def train(train_x,
          train_y,
          n_devices,
          output_device,
          preconditioner_size,
          n_training_iter,
):
    likelihood = gpytorch.likelihoods.GaussianLikelihood().to(output_device)
    model = ExactGPModel(train_x, train_y, likelihood, n_devices).to(output_device)
    model.train()
    likelihood.train()
    
    optimizer = FullBatchLBFGS(model.parameters(), lr=0.1)
    # "Loss" for GPs - the marginal log likelihood
    mll = gpytorch.mlls.ExactMarginalLogLikelihood(likelihood, model)

    
    with gpytorch.settings.max_preconditioner_size(preconditioner_size):

        def closure():
            optimizer.zero_grad()
            output = model(train_x)
            loss = -mll(output, train_y)
            return loss

        loss = closure()
        loss.backward()

        for i in range(n_training_iter):
            options = {'closure': closure, 'current_loss': loss, 'max_ls': 10}
            loss, _, _, _, _, _, _, fail = optimizer.step(options)
            
            print('Iter %d/%d - Loss: %.3f   lengthscale: %.3f   noise: %.3f' % (
                i + 1, n_training_iter, loss.item(),
                model.covar_module.module.base_kernel.lengthscale.item(),
                model.likelihood.noise.item()
            ))
            
            if fail:
                print('Convergence reached!')
                break
    
    print(f"Finished training on {train_x.size(0)} data points using {n_devices} GPUs.")
    return model, likelihood

    model, likelihood = train(train_x, train_y,
                          n_devices=n_devices, output_device=output_device,
                          preconditioner_size=100,
                          n_training_iter=20)


```

** Stack trace/error message **
```
---------------------------------------------------------------------------
RuntimeError                              Traceback (most recent call last)
Cell In [6], line 1
----> 1 model, likelihood = train(train_x, train_y,
      2                           n_devices=n_devices, output_device=output_device,
      3                           preconditioner_size=100,
      4                           n_training_iter=20)

Cell In [5], line 42, in train(train_x, train_y, n_devices, output_device, preconditioner_size, n_training_iter)
     39     loss = -mll(output, train_y)
     40     return loss
---> 42 loss = closure()
     43 loss.backward()
     45 for i in range(n_training_iter):

Cell In [5], line 39, in train.<locals>.closure()
     37 optimizer.zero_grad()
     38 output = model(train_x)
---> 39 loss = -mll(output, train_y)
     40 return loss

File ~/Software/gpytorch/gpytorch/module.py:82, in Module.__call__(self, *inputs, **kwargs)
     81 def __call__(self, *inputs, **kwargs) -> Union[Tensor, Distribution, LinearOperator]:
---> 82     outputs = self.forward(*inputs, **kwargs)
     83     if isinstance(outputs, list):
     84         return [_validate_module_outputs(output) for output in outputs]

File ~/Software/gpytorch/gpytorch/mlls/exact_marginal_log_likelihood.py:82, in ExactMarginalLogLikelihood.forward(self, function_dist, target, *params, **kwargs)
     79     raise ValueError("NaN observation policy 'fill' is not supported by ExactMarginalLogLikelihood!")
     81 # Get the log prob of the marginal distribution
---> 82 res = output.log_prob(target)
     83 res = self._add_other_terms(res, params)
     85 # Scale by the amount of data we have

File ~/Software/gpytorch/gpytorch/distributions/multivariate_normal.py:250, in MultivariateNormal.log_prob(self, value)
    248 # Get log determininant and first part of quadratic form
    249 covar = covar.evaluate_kernel()
--> 250 inv_quad, logdet = covar.inv_quad_logdet(inv_quad_rhs=diff.unsqueeze(-1), logdet=True)
    252 res = -0.5 * sum([inv_quad, logdet, diff.size(-1) * math.log(2 * math.pi)])
    253 return res

File ~/Software/gpytorch/.venv/lib/python3.13/site-packages/linear_operator/operators/_linear_operator.py:1756, in LinearOperator.inv_quad_logdet(self, inv_quad_rhs, logdet, reduce_inv_quad)
   1753 if inv_quad_rhs is not None:
   1754     args = [inv_quad_rhs] + list(args)
-> 1756 preconditioner, precond_lt, logdet_p = self._preconditioner()
   1757 if precond_lt is None:
   1758     from linear_operator.operators.identity_linear_operator import IdentityLinearOperator

File ~/Software/gpytorch/.venv/lib/python3.13/site-packages/linear_operator/operators/added_diag_linear_operator.py:126, in AddedDiagLinearOperator._preconditioner(self)
    124 if self._q_cache is None:
    125     max_iter = settings.max_preconditioner_size.value()
--> 126     self._piv_chol_self = self._linear_op.pivoted_cholesky(rank=max_iter)
    127     if torch.any(torch.isnan(self._piv_chol_self)).item():
    128         warnings.warn(
    129             "NaNs encountered in preconditioner computation. Attempting to continue without preconditioning.",
    130             NumericalWarning,
    131         )

File ~/Software/gpytorch/.venv/lib/python3.13/site-packages/linear_operator/operators/_linear_operator.py:1973, in LinearOperator.pivoted_cholesky(self, rank, error_tol, return_pivots)
   1952 r"""
   1953 Performs a partial pivoted Cholesky factorization of the (positive definite) LinearOperator.
   1954 :math:`\mathbf L \mathbf L^\top = \mathbf K`.
   (...)
   1970     https://www.sciencedirect.com/science/article/pii/S0168927411001814
   1971 """
   1972 func = PivotedCholesky.apply
-> 1973 res, pivots = func(self.representation_tree(), rank, error_tol, *self.representation())
   1975 if return_pivots:
   1976     return res, pivots

File ~/Software/gpytorch/.venv/lib/python3.13/site-packages/torch/autograd/function.py:583, in Function.apply(cls, *args, **kwargs)
    580 if not torch._C._are_functorch_transforms_active():
    581     # See NOTE: [functorch vjp and autograd interaction]
    582     args = _functorch.utils.unwrap_dead_wrappers(args)
--> 583     return super().apply(*args, **kwargs)  # type: ignore[misc]
    585 if not is_setup_ctx_defined:
    586     raise RuntimeError(
    587         "In order to use an autograd.Function with functorch transforms "
    588         "(vmap, grad, jvp, jacrev, ...), it must override the setup_context "
    589         "staticmethod. For more details, please see "
    590         "https://pytorch.org/docs/main/notes/extending.func.html"
    591     )

File ~/Software/gpytorch/.venv/lib/python3.13/site-packages/linear_operator/functions/_pivoted_cholesky.py:78, in PivotedCholesky.forward(ctx, representation_tree, max_iter, error_tol, *matrix_args)
     75 # Populater L[... m:, m] with L[..., m:, m] * L[..., m, m].sqrt()
     76 if m + 1 < matrix_shape[-1]:
     77     # Get next row of the permuted matrix
---> 78     row = apply_permutation(matrix, pi_m.unsqueeze(-1), right_permutation=None).squeeze(-2)
     79     pi_i = permutation[..., m + 1 :].contiguous()
     81     L_m_new = row.gather(-1, pi_i)

File ~/Software/gpytorch/.venv/lib/python3.13/site-packages/linear_operator/utils/permutation.py:80, in apply_permutation(matrix, left_permutation, right_permutation)
     76     right_permutation = torch.arange(matrix.size(-1), device=matrix.device)
     78 # Apply permutations
     79 return to_dense(
---> 80     matrix.__getitem__(
     81         (
     82             *batch_idx,
     83             left_permutation.unsqueeze(-1),
     84             right_permutation.unsqueeze(-2),
     85         )
     86     )
     87 )

File ~/Software/gpytorch/.venv/lib/python3.13/site-packages/linear_operator/operators/_linear_operator.py:2855, in LinearOperator.__getitem__(self, index)
   2849 # Convert all indices into tensor indices
   2850 (
   2851     *new_batch_indices,
   2852     new_row_index,
   2853     new_col_index,
   2854 ) = _convert_indices_to_tensors(self, flattened_orig_indices)
-> 2855 res = self._get_indices(new_row_index, new_col_index, *new_batch_indices)
   2856 # Now un-flatten tensor indices
   2857 if len(tensor_index_shape) > 1:  # Do we need to unflatten?

File ~/Software/gpytorch/.venv/lib/python3.13/site-packages/linear_operator/operators/cat_linear_operator.py:214, in CatLinearOperator._get_indices(self, row_index, col_index, *batch_indices)
    210 for linear_op_idx, sub_index in zip(linear_op_indices, sub_indices):
    211     sub_index[self.cat_dim] = sub_index[self.cat_dim] - self.cat_dim_cum_sizes[linear_op_idx]
    213 res_list = [
--> 214     linear_op._get_indices(sub_index[-2], sub_index[-1], *sub_index[:-2])
    215     for linear_op, sub_index in zip(linear_ops, sub_indices)
    216 ]
    217 if len(res_list) == 1:
    218     return res_list[0].view(target_shape).to(self.device)

File ~/Software/gpytorch/.venv/lib/python3.13/site-packages/linear_operator/operators/dense_linear_operator.py:50, in DenseLinearOperator._get_indices(self, row_index, col_index, *batch_indices)
     48 def _get_indices(self, row_index: IndexType, col_index: IndexType, *batch_indices: IndexType) -> torch.Tensor:
     49     # Perform the __getitem__
---> 50     res = self.tensor[(*batch_indices, row_index, col_index)]
     51     return res

RuntimeError: indices should be either on cpu or on the same device as the indexed tensor (cuda:1)
```

## Expected Behavior

The example notebook should run and complete the training successfully.

## System information

**Please complete the following information:**
- <!-- GPyTorch Version (run `print(gpytorch.__version__)` --> GPyTorch 1.15.1
- <!-- PyTorch Version (run `print(torch.__version__)` --> PyTorch 2.0.1+cu117
- <!-- Computer OS --> Ubuntu Linux

## Additional context
Add any other context about the problem here.

## PR Review Comments

**[user]** on `gpytorch/likelihoods/multitask_gaussian_likelihood.py`:

```suggestion
        self, shape: torch.Size, add_noise: Optional[bool] = True, interleaved: bool = True, *params, **kwargs
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
