# GH870_pandas_64791: BUG: Fix float16 overflow in nanmean/nansum by upcasting to float64 (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest pandas/tests/frame/test_reductions.py pandas/tests/test_nanops.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
