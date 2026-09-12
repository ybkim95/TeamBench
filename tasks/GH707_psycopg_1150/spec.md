# GH707_psycopg_1150: fix buffer in binary copy — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/psycopg/psycopg

## PR Description

[user] Here my attempt to fix the potential buffer corruption. It ensures buffer integrity on row level for both the c and the python version.

Shall fix https://github.com/psycopg/psycopg/discussions/1147.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
