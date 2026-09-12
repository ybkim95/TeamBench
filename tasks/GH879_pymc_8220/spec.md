# GH879_pymc_8220: Fix crash in vectorize_over_posterior when using ZeroSumNormal distributions — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pymc-devs/pymc/issues/8219
- Repo: https://github.com/pymc-devs/pymc

## Issue Description

### Describe the issue:

`vectorize_over_posterior` raises `AttributeError: 'RandomGeneratorType' object has no attribute 'dtype'` when the model contains a `ZeroSumNormal`. Replacing `pm.ZeroSumNormal` with `pm.Normal` in the same model works without error.

### Reproduceable code example:

```python
import pymc as pm
from pymc.sampling.forward import vectorize_over_posterior

with pm.Model() as model:
    intercept = pm.ZeroSumNormal("intercept", sigma=1.0, shape=2)
    mu = intercept
    sigma = pm.HalfNormal("sigma", sigma=1.0)
    pm.Normal("y", mu=mu, sigma=sigma, observed=[0.0, 0.0], shape=2)
    idata = pm.sample_prior_predictive(10, var_names=["intercept", "sigma"])
    idata.add_groups({"posterior": idata.prior})

vectorize_over_posterior(
    outputs=[mu],
    posterior=idata.posterior,
    input_rvs=model.free_RVs,
)
```

### Error message:

```shell
Traceback (most recent call last):
  File "<string>", line 13, in <module>
  File "pymc/sampling/forward.py", line 1059, in vectorize_over_posterior
    replace_dict[rv] = change_dist_size(rv, new_size=batch_shape, expand=True)
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "pymc/distributions/shape_utils.py", line 285, in change_dist_size
    new_dist = _change_dist_size(op, dist, new_size=new_size, expand=expand)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "functools.py", line 912, in wrapper
    return dispatch(args[0].__class__)(*args, **kw)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "pymc/distributions/shape_utils.py", line 312, in change_rv_size
    new_rv = rv_node.op(*dist_params, size=new_size, dtype=rv.type.dtype)
                                                           ^^^^^^^^^^^^^
AttributeError: 'RandomGeneratorType' object has no attribute 'dtype'
```

### PyMC version information:

<details>
PyMC Version: 5.28.2+2.g8a1896bad (Github main)
PyTensor Version: 2.38.2
Python Version: 3.12
Operating system: macOS (ARM64)
How did you install PyMC: pixi (conda-forge)
</details>

### Context for the issue:

Related to #7889

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

[user] Here, Fix a crash in change_rv_size when some random variables (like ZeroSumNormal) don’t have a dtype.
Simply we can check if dtype exists before passing it, instead of assuming it’s always there in shape_utils.py in distributions one .
Does this approach align with expectations?
Like this :-
In shape_utils.py in change_rv_size()

<img width="1085" height="380" alt="Image" src="https://github.com/user-attachments/assets/5ec5c86c-c258-404a-b78f-0f8513e2fc26" />

and create test file for this in test_forward.py

## PR Review Comments

**[user]** on `tests/sampling/test_forward.py`:

should be enough to test change_dist_size works for zsn (I thought we already tested it but apparently not)

**[user]** on `tests/sampling/test_forward.py`:

Changes addressed as per the requirement 
PR description updated as per changes and  test created to check change_dist_size works on ZeroSumNormal .

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
