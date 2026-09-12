# GH1220_darts_3044: Fix failing RNN dtype test (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest darts/tests/models/forecasting/test_torch_forecasting_model.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
