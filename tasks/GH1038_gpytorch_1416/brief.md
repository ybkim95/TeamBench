# GH1038_gpytorch_1416: Make NGD is compatible with batch-mode variational GPs (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest test/variational/test_variational_strategy.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
