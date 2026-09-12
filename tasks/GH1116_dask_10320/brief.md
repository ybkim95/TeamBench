# GH1116_dask_10320: Add missing 'not in' predicate support to `read_parquet` (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest dask/dataframe/io/tests/test_parquet.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
