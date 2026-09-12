# GH1214_airflow_64120: Fix Task SDK Connection extras from URI constructor (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest task-sdk/tests/task_sdk/definitions/test_connection.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
