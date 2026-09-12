# GH1082_gpytorch_1528: Speed up SGPR covariances — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/cornellius-gp/gpytorch

## PR Description

Addresses problem in #1515 . [user] - can you check out the `faster_sgpr_covar` branch and make sure that this fix works for you? If so, then we'll cut a bug fix release that should hopefully fix these SGPR issues once and for all :)

## PR Review Comments

**[user]** on `gpytorch/models/exact_prediction_strategies.py`:

In 6 months is this going to be the next `if "variational" in param_name:`?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
