# GH1141_scipy_24108: Fix endpoints normalization for assoc_legendre_p (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest scipy/special/tests/test_legendre.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
