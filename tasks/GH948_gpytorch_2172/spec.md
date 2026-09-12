# GH948_gpytorch_2172: MMVN.to_data_independent_dist returns correct variance for non-interleaved MMVN distributions. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/cornellius-gp/gpytorch/issues/2072
- Repo: https://github.com/cornellius-gp/gpytorch

## Issue Description

Greetings Devs and Community! I am trying to setup a basic multi-input multi-output variational GP (essentially modifying the Mulit-output Deep GP example) with 2 inputs and 2 outputs. In this demonstration I use the following equations:

_y1 = sin(2\*pi\*x1)_
_y2 = -2.5cos(2\*pi\*x2^2)\*exp(-2\*x1)_

100 randomly drawn training samples from the unit square bound by (0,0), (0,1), (1,0), (1,1) are used to train the MIMO (2-input 2 output) model. I then plot 4 figures as follows. In each output image, the true (analytical) result is shown via a dotted line and the solid line is GPyTorch's output, with the shaded region denoting the 2 sigma band.

The top row: _x1 = 0 to 1, x2 = 0.5_
The bottom row: _x1 = 0.5, x2 = 0 to 1_

The individual plots (titles will help) show the variation of _y1_ (Left column) and _y2_ (Right) along the changing _x_ (as shown).

Notice that the variances look very weird with there being a distinct change in the pattern halfway through. The change pattern is dissimilar across the outputs as well. However the means seem to be doing a brilliant job.

I was curious if anyone could shed some light as to what's up with the variances? Am I setting it up wrong?

GPyTorch version: 1.6.0

```
# import os
import torch
# import tqdm
import math
import gpytorch
# from torch.nn import Linear
from gpytorch.means import ConstantMean, LinearMean
from gpytorch.kernels import MaternKernel, ScaleKernel
from gpytorch.variational import VariationalStrategy, CholeskyVariationalDistribution \
    # , LMCVariationalStrategy
from gpytorch.distributions import MultivariateNormal
from gpytorch.models.deep_gps import DeepGPLayer, DeepGP
from gpytorch.mlls import DeepApproximateMLL, VariationalELBO
from gpytorch.likelihoods import MultitaskGaussianLikelihood
from matplotlib import pyplot as plt

## RUN PARAMETER

smoke_test = False

training_pts = 100

## TRAINING DATA

train_x = torch.stack([torch.rand(training_pts), torch.rand(training_pts)],-1)

train_y = torch.stack([
    torch.sin((2 * math.pi)*train_x[:,0]),
    -2.5*torch.cos((2 * math.pi)*train_x[:,1]**2)*torch.exp(-2*train_x[:,0]),
    ],-1)

num_tasks = train_y.size(-1)

## GENERATING GP SIMILAR TO THAT IN TUTORIAL (not deep)

class DGPHiddenLayer(DeepGPLayer):
    def __init__(self, input_dims, output_dims, num_inducing=128, linear_mean=True):
        inducing_points = torch.randn(output_dims, num_inducing, input_dims)
        batch_shape = torch.Size([output_dims])

        variational_distribution = CholeskyVariationalDistribution(
            num_inducing_points=num_inducing,
            batch_shape=batch_shape
        )
        variational_strategy = VariationalStrategy(
            self,
            inducing_points,
            variational_distribution,
            learn_inducing_locations=True
        )

        super().__init__(variational_strategy, input_dims, output_dims)
        self.mean_module = LinearMean(input_dims) if linear_mean else ConstantMean()
        self.covar_module = ScaleKernel(
            MaternKernel(nu=2.5, batch_shape=batch_shape, ard_num_dims=input_dims),
            batch_shape=batch_shape, ard_num_dims=None
        )

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return MultivariateNormal(mean_x, covar_x)

class MultitaskDeepGP(DeepGP):
    def __init__(self, train_x_shape):
        gp_layer = DGPHiddenLayer(
            input_dims=train_x_shape[-1],
            output_dims=num_tasks,
            linear_mean=True
        )

        super().__init__()

        self.gp_layer = gp_layer

        # We're going to use a ultitask likelihood instead of the standard GaussianLikelihood
        self.likelihood = MultitaskGaussianLikelihood(num_tasks=num_tasks)

    def forward(self, inputs):
        output = self.gp_layer(inputs)
        return output

    def predict(self, test_x):
        with torch.no_grad():

            # The output of the model is a multitask MVN, where both the data points
            # and the tasks are jointly distributed
            # To compute the marginal predictive NLL of each data point,
            # we will call `to_data_independent_dist`,
            # which removes the data cross-covariance terms from the distribution.
            preds = model.likelihood(model(test_x)).to_data_independent_dist()

        return preds.mean.mean(0), preds.variance.mean(0)

## TRAINING MODEL

model = MultitaskDeepGP(train_x.shape)

model.train()
optimizer = torch.optim.Adam(model.parameters(), lr=0.1)
mll = DeepApproximateMLL(VariationalELBO(model.likelihood, model, num_data=train_y.size(0)))

num_epochs = 10 if smoke_test else 200

for i in range(num_epochs):
    optimizer.zero_grad()
    output = model(train_x)
    loss = -mll(output, train_y)
    loss.backward()
    optimizer.step()
    
## TESTING ON DATA WHERE x1 = 0-1, x2 = 0.5
    
test_x = torch.stack([torch.linspace(0, 1, 25), torch.ones(25)*0.5],-1)   
test_y = torch.stack([
    torch.sin((2 * math.pi)*test_x[:,0]),
    -2.5*torch.cos((2 * math.pi)*test_x[:,1]**2)*torch.exp(-2*test_x[:,0]),
    ],-1)
    
model.eval()
with torch.no_grad(), gpytorch.settings.fast_pred_var():
    mean, var = model.predict(test_x)
    lower = mean - 2 * var.sqrt()
    upper = mean + 2 * var.sqrt()

# Plot results
fig, ax = plt.subplots(figsize=(8, 6), dpi=240)

plt.subplot(2,2,1)
plt.title('y1 vs x1 : x1 = 0-1, x2 = 0.5')
plt.plot(test_x[:,0].numpy(), test_y[:,0].numpy(), ':k')
plt.plot(test_x[:,0].numpy(), mean[:,0].numpy(), 'k')
plt.fill_between(test_x[:,0].numpy(), lower[:,0].numpy(), upper[:,0].numpy(), facecolor='k', alpha=0.2)
plt.xlabel('x1')
plt.ylabel('y1')
plt.legend(['True','Predicted','2 Sigma'])

plt.subplot(2,2,2)
plt.title('y2 vs x1 : x1 = 0-1, x2 = 0.5')
plt.plot(test_x[:,0].numpy(), test_y[:,1].numpy(), ':k')
plt.plot(test_x[:,0].numpy(), mean[:,1].numpy(), 'k')
plt.fill_between(test_x[:,0].numpy(), lower[:,1].numpy(), upper[:,1].numpy(), facecolor='k', alpha=0.2)
plt.xlabel('x1')
plt.ylabel('y2')
plt.legend(['True','Predicted','2 Sigma'])

## TESTING ON DATA WHERE x1 = 0.5, x2 = 0-1

test_x = torch.stack([torch.ones(25)*0.5, torch.linspace(0, 1, 25)],-1)
test_y = torch.stack([
    torch.sin((2 * math.pi)*test_x[:,0]),
    -2.5*torch.cos((2 * math.pi)*test_x[:,1]**2)*torch.exp(-2*test_x[:,0]),
    ],-1)

model.eval()
with torch.no_grad(), gpytorch.settings.fast_pred_var():
    mean, var = model.predict(test_x)
    lower = mean - 2 * var.sqrt()
    upper = mean + 2 * var.sqrt()

plt.subplot(2,2,3)
plt.title('y1 vs x2 : x1 = 0.5, x2 = 0-1')
plt.plot(test_x[:,1].numpy(), test_y[:,0].numpy(), ':k')
plt.plot(test_x[:,1].numpy(), mean[:,0].numpy(), 'k')
plt.fill_between(test_x[:,1].numpy(), lower[:,0].numpy(), upper[:,0].numpy(), facecolor='k', alpha=0.2)
plt.xlabel('x2')
plt.ylabel('y1')
plt.legend(['True','Predicted','2 Sigma'])

plt.subplot(2,2,4)
plt.title('y2 vs x2 : x1 = 0.5, x2 = 0-1')
plt.plot(test_x[:,1].numpy(), test_y[:,1].numpy(), ':k')
plt.plot(test_x[:,1].numpy(), mean[:,1].numpy(), 'k')
plt.fill_between(test_x[:,1].numpy(), lower[:,1].numpy(), upper[:,1].numpy(), facecolor='k', alpha=0.2)
plt.xlabel('x2')
plt.ylabel('y2')
plt.legend(['True','Predicted','2 Sigma'])

plt.tight_layout()
```

![image](https://user-images.githubusercontent.com/58831654/180029583-86e38d88-9e2e-4879-95a6-c7c09c300b58.png)

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

This took a bit of digging, but it actually is a bug on our end. I'll put up a PR.

### Comment 2 ([user]):

Hi 👋 
I have the same issue but with Exact inference instead of Variational, is the PR out? I don't see it linked to this issue. I'm able to help put up a PR for this with your indications. Thank you!

### Comment 3 ([user]):

[user] I don't think this issue is related... this was specific to variational DeepGPs.

I do realize though that this issue was closed by PR #2123 (I accidentally linked it to the wrong issue though, so this was never marked as closed!)

[user] when you get the chance, see if your issue is fixed by #2123 . It should be available on the latest stable release of GPyTorch.

### Comment 4 ([user]):

[user] I will wait for the next stable release and get back. Using pip to upgrade takes it to 1.8.1 which is an older release if I am not mistaken!

### Comment 5 ([user]):

[user] the latest stable version on PyPi is 1.9.0. https://pypi.org/project/gpytorch/
Maybe you are using an older version of Python? I think that 1.9.0 requires Python 3.8

### Comment 6 ([user]):

[user] , I did overlook that! This is my result (using the same demo code). The variance issue seems to persist.

Python: 3.8.13
Torch: 1.12.1
GPyTorch: 1.9.0

![image](https://user-images.githubusercontent.com/58831654/193908829-a9e5cbd7-5fea-4e4a-ad06-018288f5638c.png)

### Comment 7 ([user]):

Hmm okay let's re-open the issue and I'll take another look.

### Comment 8 ([user]):

I think the bug will be fixed (for real this time) with #2172.

### Comment 9 ([user]):

I'll give it a check, which build version should I get for this?

### Comment 10 ([user]):

[user] the latest version on master (it's not available on a stable release yet).

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
