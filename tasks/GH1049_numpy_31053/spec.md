# GH1049_numpy_31053: BUG: avoid warning on ufunc with where=True and no output — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/numpy/numpy

## PR Description

Backport of #31045.

Alternative fix for gh-31030. This does not change that `out=None` is removed from what is passed to the ufunc, but ensures that if from the ufunc one calls the original function with the original keyword arguments, there will only be a warning about a missing `out` argument if `where!=True`. Hence, the net effect is that the warning introduced in gh-29813 will no longer fire if there is no risk of uninitialized output.

(No AI was used.)

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
