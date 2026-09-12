# GH895_gpytorch_1919: Fix bug with PeriodicKernel.diag() — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/cornellius-gp/gpytorch/issues/1915
- Repo: https://github.com/cornellius-gp/gpytorch

## Issue Description

# 🐛 Bug

Hello, 
I have a problem with the gpytorch Periodickernel.
When triying to call the diag() method, it yiels to a runtime error.
This leads to the problem that no confidence region or predictive variance can be computed later for predictions.
That happens both for few and large data.
I am not sure if this is a bug or am I doing something wrong here?

## To reproduce

** Code snippet to reproduce **
covar_module = gpytorch.kernels.PeriodicKernel()
x1 = torch.randn(50)
lazy_covar_matrix = covar_module(x1) # Returns a RootLazyTensor
lazy_covar_matrix.diag()

** Stack trace/error message **
---------------------------------------------------------------------------
RuntimeError                              Traceback (most recent call last)
/tmp/ipykernel_43664/910117771.py in <module>
      3 x1 = torch.randn(50)
      4 lazy_covar_matrix = covar_module(x1) # Returns a RootLazyTensor
----> 5 lazy_covar_matrix.diag()

~/anaconda3/lib/python3.8/site-packages/gpytorch/utils/memoize.py in g(self, *args, **kwargs)
     57         kwargs_pkl = pickle.dumps(kwargs)
     58         if not _is_in_cache(self, cache_name, *args, kwargs_pkl=kwargs_pkl):
---> 59             return _add_to_cache(self, cache_name, method(self, *args, **kwargs), *args, kwargs_pkl=kwargs_pkl)
     60         return _get_from_cache(self, cache_name, *args, kwargs_pkl=kwargs_pkl)
     61 

~/anaconda3/lib/python3.8/site-packages/gpytorch/lazy/lazy_evaluated_kernel_tensor.py in diag(self)
    309             expected_shape = self.shape[:-1]
    310             if res.shape != expected_shape:
--> 311                 raise RuntimeError(
    312                     "The kernel {} is not equipped to handle and diag. Expected size {}. "
    313                     "Got size {}".format(self.kernel.__class__.__name__, expected_shape, res.shape)

RuntimeError: The kernel PeriodicKernel is not equipped to handle and diag. Expected size torch.Size([50]). Got size torch.Size([50, 50])

## Expected Behavior

Should return the diagonal of the kernel.

## System information

**Please complete the following information:**
GPyTorch Version (run `print(gpytorch.__version__)` 
1.6.0
PyTorch Version (run `print(torch.__version__)` 
1.10.0
Computer OS
Windows 10

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Thanks for catching this. I'm taking a look at this.

## PR Review Comments

**[user]** on `gpytorch/kernels/periodic_kernel.py`:

Should this be the following?
```suggestion
        diff = self.covar_dist(x1_, x2_, diag=diag, last_dim_is_batch=last_dim_is_batch, **params)
```

**[user]** on `gpytorch/kernels/periodic_kernel.py`:

This should be `True`, since we end up manually summing over the dimensions of the kernel. I added an explanatory comment.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
