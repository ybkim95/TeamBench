# GH982_statsmodels_9398: BUG: Ensure hessian is skipped (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest statsmodels/discrete/tests/test_conditional.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
