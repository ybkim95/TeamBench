# GH970_gpytorch_1312: Fix shape issue for MMVN with broadcasted means — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/cornellius-gp/gpytorch

## PR Description

If I have a MMVN with `mean.shape = [1 x d]` and `cover.shape = `[nd x nd]`, I would expect the singleton dimension in the mean to broadcast. Similarly for `mean.shape = [n x 1]` and `cover.shape = `[nd x nd]`.

This PR fixes a small bug and allows for this broadcasting.

## PR Review Comments

**[user]** on `gpytorch/distributions/multitask_multivariate_normal.py`:

Should we for good measure add a check that `covariance_matrix.size(-1)` is a multiple of `mean.size(-1)`? Otherwise this could result in some hard-to-debug errors...

**[user]** on `gpytorch/distributions/multitask_multivariate_normal.py`:

Yeah that makes sense. I'll update it

**[user]** on `gpytorch/distributions/multitask_multivariate_normal.py`:

Updated

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
