# GH1016_scikit_learn_17575: FIX escape double quotes when exporting tree with Graphviz (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest sklearn/tree/tests/test_export.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
