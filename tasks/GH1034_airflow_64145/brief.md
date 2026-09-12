# GH1034_airflow_64145: Fix FAB DB manager discovery in migration-only contexts (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest airflow-core/tests/unit/utils/test_db_manager.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
