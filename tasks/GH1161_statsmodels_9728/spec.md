# GH1161_statsmodels_9728: BUG: Pass alpha to plot_predict — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/statsmodels/statsmodels/issues/9705
- Repo: https://github.com/statsmodels/statsmodels

## Issue Description

This PR fixes a bug in `plot_predict` where the confidence interval width does not change when specifying a custom `alpha`.

`plot_predict` currently calls `pred.conf_int(alpha)` positionally, but in `conf_int` the first positional argument is `obs`, not `alpha`. This means the user-provided `alpha` is ignored and the default value `0.05` is always used.

This PR changes the call to:

    pred.conf_int(alpha=alpha)

so that the correct confidence level is applied.

Closes #9693.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Good start, can you add a test that will check?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
