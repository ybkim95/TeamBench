# GH1004_dask_11665: Fix filtering on parquet file containing a struct column (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest dask/dataframe/io/tests/test_parquet.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
