# GH72_pytest_14299: Remove `PytestRemovedIn9Warning` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pytest-dev/pytest/issues/13893
- Repo: https://github.com/pytest-dev/pytest

## Issue Description

Now that 9.0 is out, we should remove the pytest 9 removed features. According to our deprecation policy, 9.0 only turns the deprecation warnings to errors by default, but doesn't yet remove them. In 9.1 we can do the final removal.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
