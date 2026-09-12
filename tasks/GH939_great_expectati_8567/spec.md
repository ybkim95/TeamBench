# GH939_great_expectati_8567: [BUGFIX] Skip Snowflake FDS tests for User Forks — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/great-expectations/great_expectations

## PR Description

- [ ] Description of PR changes above includes a link to [an existing GitHub issue](https://github.com/great-expectations/great_expectations/issues)
- [ ] PR title is prefixed with one of: [BUGFIX], [FEATURE], [DOCS], [MAINTENANCE], [CONTRIB]
- [ ] Code is linted - run `invoke lint` (uses `black` + `ruff`)
- [ ] Appropriate tests and docs have been updated

For more information about contributing, see [Contribute](https://docs.greatexpectations.io/docs/contributing/contributing_checklist).

After you submit your PR, keep the page open and **monitor the statuses of the various checks made by our continuous integration process at the bottom of the page. Please fix any issues that come up** and [reach out on Slack](https://greatexpectations.io/slack) if you need help. Thanks for contributing!

## PR Review Comments

**[user]** on `tests/datasource/fluent/integration/test_sql_datasources.py`:

```suggestion
    if os.getenv("SNOWFLAKE_CI_USER_PASSWORD") or os.getenv(
        "SNOWFLAKE_CI_ACCOUNT"
    ):
        return True
    return False
```
Python's built-in truthy evaluation will give you want you want here.

**[user]** on `tests/datasource/fluent/integration/test_sql_datasources.py`:

Thank you [user]

**[user]** on `tests/datasource/fluent/integration/test_sql_datasources.py`:

```suggestion
    context: EphemeralDataContext, snowflake_creds_populated: bool
```

**[user]** on `tests/datasource/fluent/integration/test_sql_datasources.py`:

`non-blocking`
You can also build the skip directly into the fixture.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
