# GH912_sktime_4425: [BUG] temporarily skip `test_predict_quantiles` for `VAR` due to known sporadic bug #4420 (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest sktime/tests/_config.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
