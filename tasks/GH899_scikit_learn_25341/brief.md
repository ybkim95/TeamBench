# GH899_scikit_learn_25341: FIX Support read-only sparse datasets for `Tree`-based estimators (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest sklearn/ensemble/tests/test_forest.py sklearn/tree/tests/test_tree.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
