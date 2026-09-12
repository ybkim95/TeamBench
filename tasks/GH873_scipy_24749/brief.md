# GH873_scipy_24749: BUG: signal.minimum_phase: correct calculation (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest scipy/signal/tests/test_fir_filter_design.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
