# GH732_arrow_1190: added week and quarter to persian/farsi — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/arrow-py/arrow

## PR Description

There was no equivalent of week and quarter in Persian language.
I use this library and I had to use try-except to handle the week and this made me do this contribute.

## PR Review Comments

**[user]** on `tests/test_locales.py`:

missing tests for quarters, otherwise 👍

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
