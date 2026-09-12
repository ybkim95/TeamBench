# GH911_gpytorch_1592: Fix SGPR errors when testing on training data. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/cornellius-gp/gpytorch/issues/1581
- Repo: https://github.com/cornellius-gp/gpytorch

## Issue Description

# 🐛 Bug

Hi and thanks a lot for your work. Since the new release when i am trying to predict with the SGPR model, i get an error message that says that it is likely a bug in GPyTorch.

Thanks in advance.

## To reproduce

```python
import numpy as np
from tslearn.datasets import UCR_UEA_datasets
import math
import torch
import gpytorch
from gpytorch.means import ConstantMean
from gpytorch.kernels import ScaleKernel, RBFKernel, MaternKernel, InducingPointKernel
from gpytorch.distributions import MultivariateNormal

# Make plots inline
%matplotlib inline

inducing_p = 0

from gpytorch.means import ConstantMean
from gpytorch.kernels import ScaleKernel, RBFKernel, InducingPointKernel
from gpytorch.distributions import MultivariateNormal

class GPRegressionModel(gpytorch.models.ExactGP):
    def __init__(self, train_x, train_y, likelihood):
        super(GPRegressionModel, self).__init__(train_x, train_y, likelihood)
        global inducing_p
        self.mean_module = ConstantMean()
        self.base_covar_module = RBFKernel()
        self.covar_module = InducingPointKernel(self.base_covar_module, inducing_points=torch.linspace(torch.min(train_x), torch.max(train_x), inducing_p), likelihood=likelihood)

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return MultivariateNormal(mean_x, covar_x)

#global inducing_p
X_train, y_train, X_test, y_test = UCR_UEA_datasets().load_dataset('Beef')

data = np.r_[X_train, X_test]
train_y = X_train[0,:,0]  

for indx in range(1, 20):
    train_y = np.vstack([train_y, data[indx,:,0]])

train_x = torch.from_numpy(np.arange(1,train_y.shape[1]+1)).float()
train_y = torch.from_numpy(train_y).float()
train_x = (train_x - train_x.mean(0)) / train_x.std(0)

#Normalization [-1,1]
for i in range(20):
    train_y[i] = train_y[i] - torch.min(train_y[i])
    train_y[i] = 2 * (train_y[i] / torch.max(train_y[i])) - 1  

inducing_p = 2*(int(math.log2(train_y.shape[1]))+1)
# initialize likelihood and model
likelihood = []
model = []
for i in range(20):
    likelihood.append(gpytorch.likelihoods.GaussianLikelihood())
    model.append(GPRegressionModel(train_x, train_y[i], likelihood[i]))

training_iter = 50
for i in range(20):
    # Find optimal model hyperparameters
    model[i].train()
    likelihood[i].train()

    # Use the adam optimizer
    optimizer = torch.optim.Adam(model[i].parameters(), lr=0.1)  # Includes GaussianLikelihood parameters
    # "Loss" for GPs - the marginal log likelihood
    mll = gpytorch.mlls.ExactMarginalLogLikelihood(likelihood[i], model[i])

    for it in range(training_iter):
        # Zero gradients from previous iteration
        optimizer.zero_grad()
        # Output from model
        output = model[i](train_x)
        # Calc loss and backprop gradients
        loss = -mll(output, train_y[i])
        loss.backward()        
        optimizer.step()


# Get into evaluation (predictive posterior) mode
for i in range(20):
    model[i].eval()
    likelihood[i].eval()

# Test points are regularly spaced along [0,1]
# Make predictions by feeding model through likelihood
observed_pred = []
cross_covar = []
preds = []
with gpytorch.settings.max_preconditioner_size(10), torch.no_grad():
    for i in range(20):
        preds.append(model[i](train_x))               
```
## Error message
```
ValueError                                Traceback (most recent call last)
<ipython-input-20-e9aa2e04e88d> in <module>
     90 with gpytorch.settings.max_preconditioner_size(10), torch.no_grad():
     91     for i in range(20):
---> 92         preds.append(model[i](train_x))

~/miniconda3/lib/python3.8/site-packages/gpytorch/models/exact_gp.py in __call__(self, *args, **kwargs)
    317             # Make the prediction
    318             with settings._use_eval_tolerance():
--> 319                 predictive_mean, predictive_covar = self.prediction_strategy.exact_prediction(full_mean, full_covar)
    320 
    321             # Reshape predictive mean to match the appropriate event shape

~/miniconda3/lib/python3.8/site-packages/gpytorch/models/exact_prediction_strategies.py in exact_prediction(self, joint_mean, joint_covar)
    805         return (
    806             self.exact_predictive_mean(test_mean, test_train_covar),
--> 807             self.exact_predictive_covar(test_test_covar, test_train_covar),
    808         )
    809 

~/miniconda3/lib/python3.8/site-packages/gpytorch/models/exact_prediction_strategies.py in exact_predictive_covar(self, test_test_covar, test_train_covar)
    815         if not isinstance(test_train_covar, MatmulLazyTensor):
    816             # We should not hit this point of the code - this is to catch potential bugs in GPyTorch
--> 817             raise ValueError(
    818                 f"Expected SGPR output to be a MatmulLazyTensor. Got {test_train_covar.__class__.__name__} instead. "
    819                 "This is likely a bug in GPyTorch."

ValueError: Expected SGPR output to be a MatmulLazyTensor. Got LowRankRootAddedDiagLazyTensor instead. This is likely a bug in GPyTorch.
```

## System information

- GPyTorch: Version 1.4.1
- PyTorch Version: 1.8.1+cu102
- Computer OS: Ubuntu 18.04.5 LTS

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

After some investigation, it looks like the error only occurs when you make predictions on the training data. If you call `preds.append(model[i](train_x + 0.0001))` instead, there is no error.

I will put up a PR to fix this. In the meantime, you can use this hack.

### Comment 2 ([user]):

Ok, I can live with that. Thanks!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
