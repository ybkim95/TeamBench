# GH57_sqlalchemy_13155: docs: fix RelationshipProperty comparator cross-references — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/sqlalchemy/sqlalchemy/issues/13132
- Repo: https://github.com/sqlalchemy/sqlalchemy

## Issue Description

In https://docs.sqlalchemy.org/en/20/orm/internals.html#sqlalchemy.orm.RelationshipProperty.Comparator.has or https://docs.sqlalchemy.org/en/20/orm/internals.html#sqlalchemy.orm.RelationshipProperty.Comparator.any there are several references that are not resolved.

<sub>(this is mainly a reminder for myself)</sub>

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
