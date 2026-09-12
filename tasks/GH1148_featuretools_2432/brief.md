# GH1148_featuretools_2432: Fix serialization of `word_set` in `NumberOfCommonWords` (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest featuretools/tests/primitive_tests/test_feature_serialization.py featuretools/tests/primitive_tests/test_features_deserializer.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
