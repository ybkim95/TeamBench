# GH591_click_3223: Add cross-reference to tests from `test_defaults.py` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pallets/click

## PR Description

While working on https://github.com/pallets/click/issues/3145 I reviewed tests from `test_defaults.py` and discovered some sibling tests dispersed in Click test suite.

This PR is updating these tests to cross-reference them. I used this opportunity to augment the `test_basic_defaults` test with some more values to augment its coverage.

If other maintainers find these tests too similar or misplaced, I can push this PR a bit more towards moving these tests between files, merge some, or even goes further and refactor them.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
