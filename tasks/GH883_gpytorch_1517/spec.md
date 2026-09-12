# GH883_gpytorch_1517: Fix SGPR variance bug — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/cornellius-gp/gpytorch/issues/1515
- Repo: https://github.com/cornellius-gp/gpytorch

## Issue Description

# 🐛 Bug

Hi guys and thanks a lot for your work.

The predictive variance in my SGPR use cases is broken, approximately since the new release. This happens in both single output and batch mode, it doesn't throw an error but the values for the predictive variance are abnormally large and often negative. Probably a bug that slipped unnoticed through the release, maybe in the InducingPointKernel.

Thanks for your help!

## To reproduce

```python
import time
import urllib.request
import gpytorch
import torch
from gpytorch.distributions import MultivariateNormal
from gpytorch.kernels import ScaleKernel, RBFKernel, InducingPointKernel
from gpytorch.means import ConstantMean
from scipy.io import loadmat

if __name__ == '__main__':
    # Run GPyTorch SGPR + independent multioutputs example: approximate
    # https://docs.gpytorch.ai/en/v1.2.1/examples/02_Scalable_Exact_GPs/SGPR_Regression_CUDA.html
    # https://github.com/cornellius-gp/gpytorch/issues/1043
    print('Downloading \'elevators\' UCI dataset...')
    urllib.request.urlretrieve(
        'https://drive.google.com/uc?export=download&id=1jhWL3YUHvXIaftia4qeAyDwVxo6j1alk',
        '../elevators.mat')
    output_size = 1
    input_size = 18
    nb_inducing_points = 500
    data = torch.Tensor(loadmat('../elevators.mat')['data'])
    X = data[:, :-1]
    X = X - X.min(0)[0]
    X = 2 * (X / X.max(0)[0]) - 1
    X = X[:, :input_size]
    y = data[:, -1]
    # MAKE MULTIOUTPUT DATA
    y = y.reshape(-1, 1)
    y = y.repeat(1, output_size)
    input_size = X.shape[1]
    train_x = X[:10000, :].contiguous()
    train_y = y[:10000].contiguous()
    test_x = X[10000:20000, :].contiguous()
    test_y = y[10000:20000].contiguous()
    if torch.cuda.is_available():
        train_x, train_y, test_x, test_y = train_x.cuda(), train_y.cuda(), test_x.cuda(), test_y.cuda()
    # CONVERT TO BATCH GP
    train_x = train_x.repeat(output_size, 1, 1)
    train_y = train_y.transpose(-2, -1)
    test_x = test_x.repeat(output_size, 1, 1)
    test_y = test_y.transpose(-2, -1)


    class GPRegressionModel(gpytorch.models.ExactGP):
        def __init__(self, train_x, train_y, likelihood):
            super(GPRegressionModel, self).__init__(train_x, train_y,
                                                    likelihood)
            self.mean_module = ConstantMean(
                batch_shape=torch.Size([output_size]))
            self.base_covar_module = ScaleKernel(RBFKernel(
                batch_shape=torch.Size([output_size])),
                batch_shape=torch.Size([output_size]))
            inducing_points = train_x[:, :nb_inducing_points, :]
            self.covar_module = InducingPointKernel(
                self.base_covar_module,
                inducing_points=inducing_points,
                likelihood=likelihood)

        def forward(self, x):
            mean_x = self.mean_module(x)
            covar_x = self.covar_module(x)
            return MultivariateNormal(mean_x, covar_x)


    likelihood = gpytorch.likelihoods.GaussianLikelihood(
        batch_shape=torch.Size([output_size]))
    model = GPRegressionModel(train_x, train_y, likelihood)
    if torch.cuda.is_available():
        model = model.cuda()
        likelihood = likelihood.cuda()
    # Train
    training_iterations = 10
    model.train()
    likelihood.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.1)
    mll = gpytorch.mlls.ExactMarginalLogLikelihood(likelihood, model)
    for i in range(training_iterations):
        start = time.time()
        # Zero backprop gradients
        optimizer.zero_grad()
        # Get output from model
        output = model(train_x)
        # Calc loss and backprop derivatives
        loss = -mll(output, train_y).sum()
        loss.backward()
        end = time.time()
        print('Iter %d/%d - Loss: %.3f' % (
            i + 1, training_iterations, loss.item()), 'in', str(end - start))
        optimizer.step()
        torch.cuda.empty_cache()
    model.eval()
    likelihood.eval()
    with gpytorch.settings.max_preconditioner_size(10), torch.no_grad():
        with gpytorch.settings.max_root_decomposition_size(
                30), gpytorch.settings.fast_pred_var():
            preds = model(test_x)
    print(torch.mean(preds.covariance_matrix))
    print(torch.mean(preds.variance))
```

## Expected Behavior

With version 1.3.1 of GPyTorch, outputs `tensor(3.6882e-05, grad_fn=<MeanBackward0>)`, `tensor(0.0162, grad_fn=<MeanBackward0>)`.
With version 1.4.0, outputs `tensor(-2916.0591)` then hangs. 

## System information

- GPyTorch version 1.4.0
- PyTorch version 1.7.1
- Mac OS Big Sur

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

And while I'm at it, before the new release I used to initialize the value of a MultitaskGaussianLikelihood with
```python
likelihood.noise_covar.noise = torch.tensor([0.04])
likelihood.noise = torch.tensor([1e-4])
```
but now this throws an error saying `likelihood.noise_covar.noise` does not exist and `likelihood.noise` is the wrong size for `num_tasks > 1`. Any idea how I am supposed to set the value of the MultitaskGaussianLikelihood now?

Thanks!

### Comment 2 ([user]):

[user] I'm looking into the SGPR issue now - seems like something was broken by the release.

Can you please open up a separate issue for the initialization code?

### Comment 3 ([user]):

Sure!

### Comment 4 ([user]):

Thanks a lot for your quick response!

### Comment 5 ([user]):

Thanks a lot [user], can't wait for this to be merged 👍

### Comment 6 ([user]):

Hi [user], sorry to bother you again.  SGPR predictive variance works again but I feel like prediction is now much slower? To be more precise, the second big prediction call now takes as long as the first one (which was longer before because the covariance matrix was inverted).

Test code:
```python
import time
import urllib.request
import gpytorch
import torch
from gpytorch.distributions import MultivariateNormal
from gpytorch.kernels import ScaleKernel, RBFKernel, InducingPointKernel
from gpytorch.means import ConstantMean
from scipy.io import loadmat

if __name__ == '__main__':
    # Run GPyTorch SGPR + independent multioutputs example: approximate
    # https://docs.gpytorch.ai/en/v1.2.1/examples/02_Scalable_Exact_GPs/SGPR_Regression_CUDA.html
    # https://github.com/cornellius-gp/gpytorch/issues/1043
    print('Downloading \'elevators\' UCI dataset...')
    urllib.request.urlretrieve(
        'https://drive.google.com/uc?export=download&id=1jhWL3YUHvXIaftia4qeAyDwVxo6j1alk',
        '../elevators.mat')
    output_size = 5
    input_size = 18
    nb_inducing_points = 500
    data = torch.Tensor(loadmat('../elevators.mat')['data'])
    X = data[:, :-1]
    X = X - X.min(0)[0]
    X = 2 * (X / X.max(0)[0]) - 1
    X = X[:, :input_size]
    y = data[:, -1]
    # MAKE MULTIOUTPUT DATA
    y = y.reshape(-1, 1)
    y = y.repeat(1, output_size)
    print(X.shape, y.shape)
    input_size = X.shape[1]
    train_x = X[:10000, :].contiguous()
    train_y = y[:10000].contiguous()
    test_x = X[10000:20000, :].contiguous()
    test_y = y[10000:20000].contiguous()
    if torch.cuda.is_available():
        train_x, train_y, test_x, test_y = train_x.cuda(), train_y.cuda(), test_x.cuda(), test_y.cuda()
    # CONVERT TO BATCH GP
    train_x = train_x.repeat(output_size, 1, 1)
    train_y = train_y.transpose(-2, -1)
    test_x = test_x.repeat(output_size, 1, 1)
    test_y = test_y.transpose(-2, -1)
    print(train_x.shape, train_y.shape, test_x.shape)


    class GPRegressionModel(gpytorch.models.ExactGP):
        def __init__(self, train_x, train_y, likelihood):
            super(GPRegressionModel, self).__init__(train_x, train_y,
                                                    likelihood)
            self.mean_module = ConstantMean(
                batch_shape=torch.Size([output_size]))
            self.base_covar_module = ScaleKernel(RBFKernel(
                batch_shape=torch.Size([output_size])),
                batch_shape=torch.Size([output_size]))
            inducing_points = train_x[:, :nb_inducing_points, :]
            print(inducing_points.shape)
            self.covar_module = InducingPointKernel(
                self.base_covar_module,
                inducing_points=inducing_points,
                likelihood=likelihood)

        def forward(self, x):
            mean_x = self.mean_module(x)
            covar_x = self.covar_module(x)
            return MultivariateNormal(mean_x, covar_x)


    likelihood = gpytorch.likelihoods.GaussianLikelihood(
        batch_shape=torch.Size([output_size]))
    model = GPRegressionModel(train_x, train_y, likelihood)
    if torch.cuda.is_available():
        model = model.cuda()
        likelihood = likelihood.cuda()
    # Train
    training_iterations = 10
    model.train()
    likelihood.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.1)
    mll = gpytorch.mlls.ExactMarginalLogLikelihood(likelihood, model)
    start_whole = time.time()
    for i in range(training_iterations):
        start = time.time()
        # Zero backprop gradients
        optimizer.zero_grad()
        # Get output from model
        output = model(train_x)
        # Calc loss and backprop derivatives
        loss = -mll(output, train_y).sum()
        loss.backward()
        end = time.time()
        print('Iter %d/%d - Loss: %.3f' % (
            i + 1, training_iterations, loss.item()), 'in', str(end - start))
        optimizer.step()
        torch.cuda.empty_cache()
    end_whole = time.time()
    print('GPyTorch training time', str(end_whole - start_whole))
    model.eval()
    likelihood.eval()
    start = time.time()
    with gpytorch.settings.max_preconditioner_size(10), torch.no_grad():
        with gpytorch.settings.max_root_decomposition_size(
                30), gpytorch.settings.fast_pred_var():
            preds = model(test_x)
    end = time.time()
    print('predict', str(test_x.shape), 'in', str(end - start))
    start = time.time()
    with gpytorch.settings.max_preconditioner_size(10), torch.no_grad():
        with gpytorch.settings.max_root_decomposition_size(
                30), gpytorch.settings.fast_pred_var():
            preds = model(test_x)
    end = time.time()
    print('predict 2nd time', str(test_x.shape), 'in', str(end - start))
    print('Test MAE: {}'.format(torch.mean(torch.abs(preds.mean - test_y))))
    start = time.time()
    with gpytorch.settings.max_preconditioner_size(10), torch.no_grad():
        with gpytorch.settings.max_root_decomposition_size(
                30), gpytorch.settings.fast_pred_var():
            preds = model(test_x[:, 0, :])
    end = time.time()
    print('predict single point', str(test_x[:, 0, :].shape), 'in', str(end -
                                                                        start),
          '\n')
    print(torch.mean(preds.covariance_matrix))
    print(torch.mean(preds.variance))
```

Output:
```
GPyTorch training time 12.96557903289795
predict torch.Size([5, 6599, 18]) in 14.71241021156311
predict 2nd time torch.Size([5, 6599, 18]) in 17.02690601348877
Test MAE: 0.07685268670320511
predict single point torch.Size([5, 18]) in 0.34274888038635254 
```
instead of approximately 13s, 1s and 0.5s before. Maybe the covariance cache is recomputed on the second prediction?

### Comment 7 ([user]):

[user] yeah I see the issue... see the comments in PR #1528 . I think that PR should finally fix things once and for all!

### Comment 8 ([user]):

I think this was closed by #1528.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
