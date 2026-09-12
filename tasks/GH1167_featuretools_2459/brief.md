# GH1167_featuretools_2459: Fix bug with `NumWords`; add test suite (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest featuretools/tests/primitive_tests/natural_language_primitives_tests/test_num_words.py featuretools/tests/primitive_tests/test_transform_features.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
