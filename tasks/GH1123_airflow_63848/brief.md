# GH1123_airflow_63848: Fix partitioned asset events incorrectly triggering non-partition-aware Dags (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest airflow-core/tests/unit/assets/test_manager.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
