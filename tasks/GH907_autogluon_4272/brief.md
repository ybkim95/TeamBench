# GH907_autogluon_4272: [tabular] Fix LightGBM quantile predict_proba dtype (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tabular/tests/conftest.py tabular/tests/unittests/models/test_lightgbm.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
