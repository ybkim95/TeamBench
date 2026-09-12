# GH1185_airflow_62174: Order of task arguments in task definition causing error when parsing DAG (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest task-sdk/tests/task_sdk/bases/test_decorator.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
