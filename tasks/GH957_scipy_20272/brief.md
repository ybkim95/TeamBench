# GH957_scipy_20272: BUG: optimize: fix incorrect variable assignment in `_trustregion_exact.py` (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest scipy/optimize/tests/test_trustregion_exact.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
