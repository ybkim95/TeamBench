# GH947_pymc_7695: Fix bug when reusing jax logp for initial point generation — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pymc-devs/pymc

## PR Description

Fixes issue described in https://discourse.pymc.io/t/attributeerror-numpy-ndarray-object-has-no-attribute-at-when-sampling-lkj-cholesky-covariance-priors-for-multivariate-normal-models-example-with-numpyro-or-blackjax/16598/3

Caused by #7681 
CC [user] 

<!-- readthedocs-preview pymc start -->
----
📚 Documentation preview 📚: https://pymc--7695.org.readthedocs.build/en/7695/

<!-- readthedocs-preview pymc end -->

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
