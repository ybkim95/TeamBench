# GH995_scikit_learn_19490: EHN Support unit-variance whitening for `FastICA` (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest sklearn/decomposition/tests/test_fastica.py sklearn/tests/test_docstring_parameters.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
