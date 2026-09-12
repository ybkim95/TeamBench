# GH642_marshmallow_2854: feat: improve consistency of many arg with nested schema — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/marshmallow-code/marshmallow

## PR Description

For nested field, we can get some inconsistencies between `field.many` and `field.schema.many`.

Here is a proposal to handle inconsistency edge cases (see tests).

PS: Such inconsistencies have some effects on automatic  swagger generation in `flask_appbuilder` (and thus in projects using it, as `superset`).
This will solve https://github.com/apache/superset/issues/33884.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
