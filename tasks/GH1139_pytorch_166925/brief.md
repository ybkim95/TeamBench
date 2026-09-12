# GH1139_pytorch_166925: [dynamo] fix error_on_graph_break bug where non-empty checkpoint results in unwanted graph break resumption (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest test/dynamo/test_decorators.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
