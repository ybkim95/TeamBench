# GH1165_featuretools_2694: Restrict Dask and Fix Serialization Tests — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/alteryx/featuretools/issues/2693
- Repo: https://github.com/alteryx/featuretools

## PR Description

Closes #2693

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
