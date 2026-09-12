# GH916_scikit_learn_22191: FIX poisson proxy_impurity_improvement (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest sklearn/ensemble/tests/test_forest.py sklearn/tree/tests/test_tree.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
