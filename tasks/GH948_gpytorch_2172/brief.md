# GH948_gpytorch_2172: MMVN.to_data_independent_dist returns correct variance for non-interleaved MMVN distributions. (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest test/distributions/test_multitask_multivariate_normal.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
