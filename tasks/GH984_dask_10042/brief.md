# GH984_dask_10042: Fix handling of missing min/max parquet statistics during filtering (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest dask/dataframe/io/tests/test_parquet.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
