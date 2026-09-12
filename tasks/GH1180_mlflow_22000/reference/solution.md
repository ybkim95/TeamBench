# Reference solution — GH1180_mlflow_22000

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1180_mlflow_22000`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1180_mlflow_22000/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `mlflow/gateway/cli.py` (modified, +2/-2)
- `tests/telemetry/test_tracked_events.py` (modified, +5/-4)

## Diff Summary (What the Fix Changes)

### `mlflow/gateway/cli.py`
```diff
@@ -4,7 +4,7 @@
 from mlflow.gateway.config import _validate_config
 from mlflow.gateway.runner import run_app
 from mlflow.telemetry.events import GatewayStartEvent
-from mlflow.telemetry.track import record_usage_event
+from mlflow.telemetry.track import _record_event
 from mlflow.utils.os import is_windows
 
 
@@ -44,8 +44,8 @@ def commands():
     default=2,
     help="The number of workers.",
 )
-@record_usage_event(GatewayStartEvent)
 def start(config_path: str, host: str, port: str, workers: int):
     if is_windows():
         raise click.ClickException("MLflow AI Gateway does not support Windows.")
+    _record_event(GatewayStartEvent, {})
     run_app(config_path=config_path, host=host, port=port, workers=workers)
```

## Moved from `brief.md`

## Files That May Need Changes

- `mlflow/gateway/cli.py`
