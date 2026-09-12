# GH1207_darts_2907: fix unit tests for non-torch flavors (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest darts/tests/models/forecasting/test_regression_ensemble_model.py darts/tests/utils/historical_forecasts/test_historical_forecasts.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
