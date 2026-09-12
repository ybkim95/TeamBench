# GH1151_pymc_7856: Do not fail with zero-sized arrays in `dataset_to_point_list` (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tests/backends/test_arviz.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
