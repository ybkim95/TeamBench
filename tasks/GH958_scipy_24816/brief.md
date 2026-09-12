# GH958_scipy_24816: BUG: sparse.csgraph.reconstruct_path: raise for non-integral predecessors (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest scipy/sparse/csgraph/tests/test_conversions.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
