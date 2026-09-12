# GH1127_FLAML_1522: Fix test_no_optuna reinstalling optuna at wrong version (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest test/tune/test_searcher.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
