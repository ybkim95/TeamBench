# GH1183_mlflow_21797: Fix re-enqueued jobs to respect workspace disabled flag (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tests/server/jobs/test_jobs.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
