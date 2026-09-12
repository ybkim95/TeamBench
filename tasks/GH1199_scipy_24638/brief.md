# GH1199_scipy_24638: TST: fix tests for array-api-strict 2.5 / Array API 2025.12 spec (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest scipy/conftest.py scipy/signal/tests/test_signaltools.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
