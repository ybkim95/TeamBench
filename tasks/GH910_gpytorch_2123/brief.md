# GH910_gpytorch_2123: Fix bug with Multitask DeepGP predictive variances. (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest test/likelihoods/test_multitask_gaussian_likelihood.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
