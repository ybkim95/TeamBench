# GH1010_great_expectati_10406: [BUGFIX] Fix Databricks SQL Regex and Like based Expectations — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/great-expectations/great_expectations

## PR Description

Regex based Expectations do not currently work for DatabricksSQL.

Added 2 expectations to the SQL datasource integration tests. Both just matching on wildcards. Even with wildcards, both of these failed previously for Databricks SQL.
1. `expect_column_values_to_match_regex`
2. `expect_column_values_to_match_like_pattern`

## PR Review Comments

**[user]** on `great_expectations/expectations/metrics/util.py`:

The types the `dialect` object can be causes me pain 😬

**[user]** on `great_expectations/execution_engine/sqlalchemy_execution_engine.py`:

This change didn't seem to be necessary to fix the expectations.

**[user]** on `great_expectations/expectations/metrics/util.py`:

Non-blocking: Is it worth making an alias?

**[user]** on `great_expectations/expectations/metrics/util.py`:

I'd be afriad that will lock-in or encourage the behavior of using `dialect` in all these different ways.

I'd like to spend some effort eliminating or reducing the multiple types of "dialects" we provide here.
It's possible that we don't actually need to be this flexible here, but I haven't done a deep dive on that.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
