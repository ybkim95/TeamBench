# GH1064_pymc_7607: Bump numpy version due to use of `Generator.spawn` only available in `>=1.25` (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tests/distributions/test_custom.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
