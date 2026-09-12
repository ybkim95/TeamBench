# GH879_pymc_8220: Fix crash in vectorize_over_posterior when using ZeroSumNormal distributions (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tests/sampling/test_forward.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
