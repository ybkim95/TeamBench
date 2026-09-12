# GH862_pytorch_lightni_21192: Fix lightning cli crashing when trainer defaults contain callback (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tests/tests_pytorch/test_cli.py tests/tests_pytorch/trainer/connectors/test_callback_connector.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
