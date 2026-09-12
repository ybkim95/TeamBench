# GH932_mlflow_22067: Fix assistant stream killed by unhandled `rate_limit_event` from Claude Code CLI (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tests/assistant/providers/test_claude_code_provider.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
