# GH885_sktime_2548: [BUG] Fixed bug with kmedoids (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest sktime/clustering/tests/test_k_medoids.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
