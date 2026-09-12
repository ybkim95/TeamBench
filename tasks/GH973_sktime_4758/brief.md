# GH973_sktime_4758: [BUG] allows probabilistic predictions in `DynamicFactor` in presence of exogenous variables (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest sktime/forecasting/tests/test_dynamic_factor.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
