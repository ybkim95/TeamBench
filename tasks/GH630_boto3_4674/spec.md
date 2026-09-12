# GH630_boto3_4674: Fix logging calls to defer formatting messages until needed — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/boto/boto3

## PR Description

*Issue #, if available:* Sibling of (withheld: the upstream fix is not part of the task)

*Description of changes:* This PR enables the Ruff [G (`flake8-logging-format`) group](https://docs.astral.sh/ruff/rules/#flake8-logging-format-g) and fixes the found issues.

By submitting this pull request, I confirm that you can use, modify, copy, and redistribute this contribution, under the terms of your choice.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
