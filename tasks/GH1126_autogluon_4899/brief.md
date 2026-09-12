# GH1126_autogluon_4899: [timeseries] Allow using custom distr_output with the TFT model (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest timeseries/tests/unittests/models/test_gluonts.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
