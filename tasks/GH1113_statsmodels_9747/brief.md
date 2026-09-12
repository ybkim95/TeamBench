# GH1113_statsmodels_9747: BUG: raise error for invalid endog input in emplike.DescStat (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest statsmodels/emplike/tests/test_descriptive.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
