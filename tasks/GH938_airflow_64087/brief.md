# GH938_airflow_64087: Fix DagRun._emit_dagrun_span crash on None/empty context_carrier (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest airflow-core/tests/unit/models/test_dagrun.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
