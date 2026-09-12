# Reference solution — GH932_mlflow_22067

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH932_mlflow_22067`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH932_mlflow_22067/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `mlflow/assistant/providers/claude_code.py` (modified, +3/-0)
- `tests/assistant/providers/test_claude_code_provider.py` (modified, +34/-0)

## Diff Summary (What the Fix Changes)

### `mlflow/assistant/providers/claude_code.py`
```diff
@@ -577,6 +577,9 @@ def _parse_message_to_event(self, data: dict[str, Any]) -> Event | None:
                 except KeyError as e:
                     return Event.from_error(f"Failed to parse stream_event message: {e}")
 
+            case "rate_limit_event":
+                return None
+
             case _:
                 return Event.from_error(f"Unknown message type: {message_type}")
 
```

## Moved from `brief.md`

## Files That May Need Changes

- `mlflow/assistant/providers/claude_code.py`
