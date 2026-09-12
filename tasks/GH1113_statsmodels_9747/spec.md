# GH1113_statsmodels_9747: BUG: raise error for invalid endog input in emplike.DescStat — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/statsmodels/statsmodels

## PR Description

This PR adds basic input validation to emplike.DescStat to ensure that the input data (endog) is a non-empty 1D or 2D array.

Previously, scalar, empty, or higher-dimensional inputs could be silently reshaped or lead to unclear errors later in the computation. The new validation raises a clear ValueError early, improving robustness and user feedback.

A regression test is included to cover these invalid input cases. Existing behavior for valid inputs is unchanged.

## PR Review Comments

**[user]** on `statsmodels/emplike/tests/test_descriptive.py`:

## First parameter of a method is not named 'self'

Normal methods should have 'self', rather than 'endog', as their first parameter.

[Show more details](https://github.com/statsmodels/statsmodels/security/code-scanning/3509)

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
