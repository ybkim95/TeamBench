# GH949_gpytorch_1446: Bug fixes to LowRank lazy tensors — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/cornellius-gp/gpytorch

## PR Description

There were no unit tests for LowRankRootLazyTensor (or its added diag variant), and there were a number of issues. Most notably, `inv_quad_logdet` was not returning the right `inv_quad` term, which caused errors when using this LazyTensor on a batched GP model.

This PR fixes these issues, and also uses `LowRankRootLazyTensor` for RFF kernels.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
