# GH1129_gpytorch_2559: Avoid unnecessary memory allocation for covariance downdate in SGPR prediction strategy — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/cornellius-gp/gpytorch

## PR Description

**Problem**
Currently in the SGPR prediction strategy the downdate term in the predictive covariance (shape ``num_test x num_test``) is constructed densely in memory causing unnecessary memory overhead.

**Fix**
Replaced the downdate term with a ``linear_operator.MatmulLinearOperator``.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
