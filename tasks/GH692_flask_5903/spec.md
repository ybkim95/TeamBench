# GH692_flask_5903: Abort if the instance folder cannot be created — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pallets/flask

## PR Description

According to the comment, the instance folder should exist in any case. But a PermissionError was ignored silently.

Since Python 3.9 is the minimum required version, it is safe to use "exist_ok" added in Python 3.2 and avoid exception handling.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
