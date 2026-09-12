# GH1014_pymc_7809: Only add `dim_length` shared variable when adding a new coordinate (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tests/model/test_core.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
