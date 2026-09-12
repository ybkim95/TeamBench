# GH1052_statsmodels_9524: BUG: Fix bug in Runs.runs_test for the case of a single run yielding … (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest statsmodels/sandbox/stats/tests/test_runs.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
