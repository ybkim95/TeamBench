# GH1180_mlflow_22000: Fix `GatewayStartEvent` to fire at startup instead of shutdown (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest tests/telemetry/test_tracked_events.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
