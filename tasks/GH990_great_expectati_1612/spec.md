# GH990_great_expectati_1612: [BUGFIX] database_store_backend does not support storing Expectations in DB — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/great-expectations/great_expectations

## PR Description

Changes proposed in this pull request:
- database_store_backend now supports storing Expectations in DB
- These changes are dependent on allowing updates to DB entries. Currently GE throws a Integrity error (psycopg2.errors.UniqueViolation) when trying to create an Expectation suite or Validation entry.

## PR Review Comments

**[user]** on `great_expectations/data_context/store/database_store_backend.py`:

```suggestion
                    f"Integrity error {str(e)} while trying to store key"
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
