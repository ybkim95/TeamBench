# GH970_gpytorch_1312: Fix shape issue for MMVN with broadcasted means (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest test/distributions/test_multitask_multivariate_normal.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
