# GH1036_FLAML_1405: fix: Fixed bug where group folds and sample weights couldn't be used together (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest test/automl/test_split.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
