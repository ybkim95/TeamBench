# GH1131_sktime_4442: [MNT] except `VECM` from `test_predict_quantiles` due to sporadic failures (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest sktime/tests/_config.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
