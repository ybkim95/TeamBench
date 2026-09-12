# GH1096_autogluon_5131: [timeseries] Avoid masking the 'scaler' param with the default 'target_scaler' value (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest timeseries/tests/unittests/models/test_mlforecast.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
