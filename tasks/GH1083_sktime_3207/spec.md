# GH1083_sktime_3207: [BUG] skip check for no. estimators in contracted classifiers — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/sktime/sktime

## PR Description

This PR removes a stochastic failure from `main` coming from checks in tests of contracted classifiers, see #3206.

#3206 should be used for finding a better resolution of the failure, this PR simply removes the problem from `main`.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
