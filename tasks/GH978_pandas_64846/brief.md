# GH978_pandas_64846: Revert "BUG: distinguish bool from int in object-dtype hash table" (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest pandas/tests/groupby/test_groupby.py pandas/tests/indexes/multi/test_indexing.py pandas/tests/indexes/object/test_indexing.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
