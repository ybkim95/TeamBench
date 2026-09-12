# GH567_poetry_10766: Add tests for `switch_working_directory` helper — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/python-poetry/poetry

## PR Description

## Summary
- add test that `switch_working_directory()` restores the original cwd when an exception is raised
- add test that `remove=True` deletes the temporary working directory after exiting the context manager

Related to python-poetry/poetry#9161

## Summary by Sourcery

Add coverage for the switch_working_directory helper behavior.

Tests:
- Add a test ensuring switch_working_directory restores the original working directory when an exception is raised inside the context.
- Add a test ensuring switch_working_directory removes the temporary working directory when used with remove=True.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
