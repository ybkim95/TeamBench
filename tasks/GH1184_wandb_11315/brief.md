# GH1184_wandb_11315: fix(launch): fallback to sh when bash is unavailable in local container runner (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tests/unit_tests/test_launch/test_runner/test_local_container.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
