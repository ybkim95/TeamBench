# GH667_pytest_14294: fixtures: find SubRequest.node eagerly — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pytest-dev/pytest

## PR Description

Currently `SubRequest.node` is a property which finds the node on every access. This is mildly expensive (need to search up the collection tree), and is almost guaranteed to be called several times (in `execute` and `finish`).

Since the node can't change, let's find the node in the ctor once and save it.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
