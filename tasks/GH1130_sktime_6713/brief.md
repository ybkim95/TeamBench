# GH1130_sktime_6713: [MNT] skip failing test `test_wrapper_series_mtype` on `gluonts` datatype (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest sktime/forecasting/tests/test_interval_wrappers.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
