# GH729_werkzeug_3038: Add a DuplicateRuleError — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pallets/werkzeug

## PR Description

This is raised if an equivalent rule is added to the matcher to an
existing rule. This should help users of the router know when they've
accidentally duplicated a match.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
