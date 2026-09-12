# GH940_great_expectati_8559: [BUGFIX] Use a randomized schema name when running snowflake tests to support concurrency (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tests/datasource/fluent/integration/test_sql_datasources.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
