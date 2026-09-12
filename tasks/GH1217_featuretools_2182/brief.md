# GH1217_featuretools_2182: Fix Woodwork 0.17.0 Integration Test Failures (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest featuretools/tests/primitive_tests/test_transform_features.py featuretools/tests/testing_utils/mock_ds.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
