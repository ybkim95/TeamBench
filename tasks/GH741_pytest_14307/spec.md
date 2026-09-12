# GH741_pytest_14307: config: slightly simplify `_set_initial_conftests` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pytest-dev/pytest

## PR Description

Rework the logic a bit to collect the anchors and only then load them. This allows inlining `_try_load_conftest` and making the logic easier to follow.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
