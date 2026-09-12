# GH1063_FLAML_1419: Fix issue with "list index out of range" when max_iter=1 (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest test/automl/test_max_iter_1.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
