# GH1038_gpytorch_1416: Make NGD is compatible with batch-mode variational GPs — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/cornellius-gp/gpytorch/issues/1300
- Repo: https://github.com/cornellius-gp/gpytorch

## Issue Description

# 🐛 Bug

size mismatch when using natural gradient in multi-output GP

## To reproduce

** Code snippet to reproduce **
```python
import math
import torch
import gpytorch
import tqdm
from matplotlib import pyplot as plt

train_x = torch.linspace(0, 1, 100)

train_y = torch.stack([
    torch.sin(train_x * (2 * math.pi)) + torch.randn(train_x.size()) * 0.2,
    torch.cos(train_x * (2 * math.pi)) + torch.randn(train_x.size()) * 0.2,
    torch.sin(train_x * (2 * math.pi)) + 2 * torch.cos(train_x * (2 * math.pi)) + torch.randn(train_x.size()) * 0.2,
    -torch.cos(train_x * (2 * math.pi)) + torch.randn(train_x.size()) * 0.2,
], -1)

print(train_x.shape, train_y.shape)

num_latents = 3
num_tasks = 4


class IndependentMultitaskGPModel(gpytorch.models.ApproximateGP):
    def __init__(self):
        # Let's use a different set of inducing points for each task
        inducing_points = torch.rand(num_tasks, 16, 1)

        # We have to mark the CholeskyVariationalDistribution as batch
        # so that we learn a variational distribution for each task
        # variational_distribution = gpytorch.variational.CholeskyVariationalDistribution(
        #     inducing_points.size(-2), batch_shape=torch.Size([num_tasks])
        # )
        variational_distribution = gpytorch.variational.NaturalVariationalDistribution(
            inducing_points.size(-2), batch_shape=torch.Size([num_tasks])
        )

        variational_strategy = gpytorch.variational.IndependentMultitaskVariationalStrategy(
            gpytorch.variational.VariationalStrategy(
                self, inducing_points, variational_distribution, learn_inducing_locations=True
            ),
            num_tasks=4,
        )

        super().__init__(variational_strategy)

        # The mean and covariance modules should be marked as batch
        # so we learn a different set of hyperparameters
        self.mean_module = gpytorch.means.ConstantMean(batch_shape=torch.Size([num_tasks]))
        self.covar_module = gpytorch.kernels.ScaleKernel(
            gpytorch.kernels.RBFKernel(batch_shape=torch.Size([num_tasks])),
            batch_shape=torch.Size([num_tasks])
        )

    def forward(self, x):
        # The forward function should be written as if we were dealing with each output
        # dimension in batch
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)


# model = MultitaskGPModel()

model = IndependentMultitaskGPModel()
likelihood = gpytorch.likelihoods.MultitaskGaussianLikelihood(num_tasks=num_tasks)

# this is for running the notebook in our testing framework
import os
smoke_test = ('CI' in os.environ)
num_epochs = 1 if smoke_test else 500


model.train()
likelihood.train()

ngd_optimizer = gpytorch.optim.NGD(model.variational_parameters(),
                                   num_data=train_y.size(0),
                                   lr=0.1)
# We use SGD here, rather than Adam. Emperically, we find that SGD is better for variational regression
optimizer = torch.optim.Adam([
    {'params': model.hyperparameters()},
    {'params': likelihood.parameters()},
], lr=0.1)

# Our loss object. We're using the VariationalELBO, which essentially just computes the ELBO
mll = gpytorch.mlls.VariationalELBO(likelihood, model, num_data=train_y.size(0))

# We use more CG iterations here because the preconditioner introduced in the NeurIPS paper seems to be less
# effective for VI.
epochs_iter = tqdm.tqdm(range(num_epochs), desc="Epoch")
for i in epochs_iter:
    # Within each iteration, we will go over each minibatch of data
    ngd_optimizer.zero_grad()
    optimizer.zero_grad()
    output = model(train_x)
    loss = -mll(output, train_y)
    epochs_iter.set_postfix(loss=loss.item())
    loss.backward()
    ngd_optimizer.step()
    optimizer.step()

# Set into eval mode
model.eval()
likelihood.eval()

# Initialize plots
fig, axs = plt.subplots(1, num_tasks, figsize=(4 * num_tasks, 3))

# Make predictions
with torch.no_grad(), gpytorch.settings.fast_pred_var():
    test_x = torch.linspace(0, 1, 51)
    predictions = likelihood(model(test_x))
    mean = predictions.mean
    lower, upper = predictions.confidence_region()

for task, ax in enumerate(axs):
    # Plot training data as black stars
    ax.plot(train_x.detach().numpy(), train_y[:, task].detach().numpy(), 'k*')
    # Predictive mean as blue line
    ax.plot(test_x.numpy(), mean[:, task].numpy(), 'b')
    # Shade in confidence
    ax.fill_between(test_x.numpy(), lower[:, task].numpy(), upper[:, task].numpy(), alpha=0.5)
    ax.set_ylim([-3, 3])
    ax.legend(['Observed Data', 'Mean', 'Confidence'])
    ax.set_title(f'Task {task + 1}')

fig.tight_layout()
plt.show()
```

** Stack trace/error message **
```bash
Traceback (most recent call last):
torch.Size([100]) torch.Size([100, 4])
Epoch:   0%|                                            | 0/500 [00:00<?, ?it/s]
Traceback (most recent call last):
  File "multi-svgp.py", line 99, in <module>
    output = model(train_x)
  File "/home/user/miniconda2/envs/torch_play/lib/python3.7/site-packages/gpytorch/models/approximate_gp.py", line 81, in __call__
    return self.variational_strategy(inputs, prior=prior)
  File "/home/user/miniconda2/envs/torch_play/lib/python3.7/site-packages/gpytorch/variational/independent_multitask_variational_strategy.py", line 47, in __call__
    function_dist = self.base_variational_strategy(x, prior=prior)
  File "/home/user/miniconda2/envs/torch_play/lib/python3.7/site-packages/gpytorch/variational/variational_strategy.py", line 166, in __call__
    return super().__call__(x, prior=prior)
  File "/home/user/miniconda2/envs/torch_play/lib/python3.7/site-packages/gpytorch/variational/_variational_strategy.py", line 114, in __call__
    self._variational_distribution.initialize_variational_distribution(prior_dist)
  File "/home/user/miniconda2/envs/torch_play/lib/python3.7/site-packages/gpytorch/variational/natural_variational_distribution.py", line 69, in initialize_variational_distribution
    self.natural_vec.data.copy_((prior_prec @ prior_mean).add_(noise))
RuntimeError: size mismatch, m1: [64 x 16], m2: [4 x 16] at /pytorch/aten/src/TH/generic/THTensorMath.cpp:41
```

## Expected Behavior

Getting similar results as in the [non-natural gradient notebook](https://docs.gpytorch.ai/en/v1.2.0/examples/04_Variational_and_Approximate_GPs/SVGP_Multitask_GP_Regression.html#Train-the-model)

## System information

**Please complete the following information:**
-  GPyTorch Version 1.2.0 
- PyTorch Version 1.6.0
-  Debian 10

## Additional context
I followed the [NGD tutorial](https://docs.gpytorch.ai/en/v1.2.0/examples/04_Variational_and_Approximate_GPs/Natural_Gradient_Descent.html) and replace the necessary code in the multi-output SVGP cases. Seems the problems come to the shape of `prior_prec` and `prior_mean`.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

This is probably a bug. I'll take a look soon.

### Comment 2 ([user]):

I tried to use natural gradient to train a DGP and got the same exception as OP. Could this be related?

### Comment 3 ([user]):

Sorry [user] for the slow work - a PR is up to fix this.

[user] - this should also fix the issue with Deep GPs, but I think Adam is a better choice for Deep GPs than NGD. NGD can be a bit unstable for non-conjugate models.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
