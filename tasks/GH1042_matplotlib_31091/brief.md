# GH1042_matplotlib_31091: BUG: Fix IndexLocator.tick_values returning values greater than vmax (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest lib/matplotlib/tests/test_ticker.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
