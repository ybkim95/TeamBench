# GH712_celery_10033: Only use exceptiongroup backport for Python < 3.11 — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/celery/celery

## PR Description

The `exceptiongroup` backport is only relevant for old enough Python versions that some distributions (e.g. Debian) no longer package it.  It seems easy enough to avoid the import where it isn't needed.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
