# GH1026_numpy_30521: BUG: validate contraction axes in tensordot (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest numpy/_core/tests/test_numeric.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
