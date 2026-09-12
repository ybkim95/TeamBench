# GH1207_darts_2907: fix unit tests for non-torch flavors — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/unit8co/darts

## PR Description

Checklist before merging this PR:
- [x] Mentioned all issues that this PR fixes or addresses.
- [x] Summarized the updates of this PR under **Summary**.
- [x] Added an entry under **Unreleased** in the [Changelog](../CHANGELOG.md). (not required)

Fixes all failing unit tests from #2894 for non-torch flavors.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
