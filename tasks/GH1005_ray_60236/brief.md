# GH1005_ray_60236: [Data] - Only return selected data columns in hive partitioned parquet files (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest python/ray/data/tests/datasource/test_parquet.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
