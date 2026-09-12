# GH971_sktime_8548: [BUG] fix `run_test_for_module` usage in `tests:libs` tag — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/sktime/sktime

## PR Description

The `run_test_for_module` usage in `tests:libs` tag was buggy - if the tag was set, it would always trigger tests for the class, even if the `ONLY_CHANGED_MODULES` flag was passed to `run_test_for_class`

The reason for this was that `run_test_for_module` was getting its parameter from the global `ONLY_CHANGED_MODULES` and not from the input of `run_test_for_class` which called it - this has been fixed.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
