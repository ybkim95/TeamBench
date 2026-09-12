# GH971_sktime_8548: [BUG] fix `run_test_for_module` usage in `tests:libs` tag (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest sktime/tests/test_switch.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
