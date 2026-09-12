# GH1162_statsmodels_9413: BUG: Ensure VAR can forecast with 0 lags (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest statsmodels/tsa/vector_ar/tests/test_var.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
