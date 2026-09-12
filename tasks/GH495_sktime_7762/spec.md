# GH495_sktime_7762: [BUG] conversion `Series`-`pd.DataFrame` to `Series`-`pd.Series` now retains original column name as attr name in `pd.Series` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/sktime/sktime/issues/7763
- Repo: https://github.com/sktime/sktime

## Issue Description

Suppose XYZ is a forecaster with y scitype of pd.Series.
If you call XYZ.fit(y) with y a pd.DataFrame with a single column, sktime is "robust" and will convert the single column DataFrame to a pd.Series. This is done in routine 'convert_MvS_to_UvS_as_Series' in datatypes/_series/_convert.py.

The problem is that in doing this, the column name from the DataFrame has been lost. It should be retained as the attr name in the new series.

This can be reproduced by calling the fit method with a 1-column DataFrame on any forecaster that has y scitype of pd.Series.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Summary from discord:

talking about `convert_MvS_to_UvS_as_Series`, and in particular line 94, `y = obj[obj.columns[0]]` and then 96 which removes the `name` attr, always.

I thought that this was to ensure consistency of round trips - there are two round trips, Series -> DataFrame -> Series, and DataFrame -> Series -> DataFrame

I agree with [user] that this seems inconsistent between input types, so keeping the name might be a better approach.

[user] opened a PR with the change here: (withheld: the upstream fix is not part of the task) - and now we are seeing if any tests fail. A full test run is needed because tihs is a central piece of code, so we need to be really sure nothing breaks.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
