# GH1090_statsmodels_9457: BUG: Correct DatetimeIndex use — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/statsmodels/statsmodels/issues/9455
- Repo: https://github.com/statsmodels/statsmodels

## Issue Description

https://github.com/statsmodels/statsmodels/blob/main/statsmodels/tsa/x13.py:430 calls `pd.DatetimeIndex` with the `start` argument, which has been deprecated. My understanding is that users are now supposed to use `pd.date_range` to accomplish something similar.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Thanks for reporting.  Fixed in main now.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
