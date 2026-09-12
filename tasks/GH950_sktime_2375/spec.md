# GH950_sktime_2375: [BUG] Fixing broken conversions from nested data frame — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/sktime/sktime

## PR Description

Attempted fix of https://github.com/alan-turing-institute/sktime/issues/2381, of broken conversions from nested data frame to other types:

* `from_nested_to_multi_index` conversion was very brittle and sensitive wrt index names. I replaced the dozens of lines with a minor variation on `pandas.explode` (which also should be much faster)

Conditional on PR (withheld: the upstream fix is not part of the task) to avoid duplicate columns coming out of `RandomIntervalSegmenter` which would break the new converter (but are not interface compliant).

Test for the duplicate column problem is introduced here:
(withheld: the upstream fix is not part of the task)

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
