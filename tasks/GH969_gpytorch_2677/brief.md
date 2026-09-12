# GH969_gpytorch_2677: Fix for #2674 - Corrected sizes for alpha in RQKernel when using Deep GPs (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest test/kernels/test_rq_kernel.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
