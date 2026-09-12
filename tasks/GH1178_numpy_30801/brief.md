# GH1178_numpy_30801: TST: fix POWER VSX feature mapping (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest numpy/_core/tests/test_cpu_features.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
