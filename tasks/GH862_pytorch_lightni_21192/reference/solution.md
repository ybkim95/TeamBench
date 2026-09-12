# Reference solution — GH862_pytorch_lightni_21192

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH862_pytorch_lightni_21192`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH862_pytorch_lightni_21192/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `src/lightning/pytorch/CHANGELOG.md` (modified, +4/-0)
- `src/lightning/pytorch/trainer/connectors/callback_connector.py` (modified, +1/-1)
- `tests/tests_pytorch/test_cli.py` (modified, +26/-0)
- `tests/tests_pytorch/trainer/connectors/test_callback_connector.py` (modified, +86/-9)

## Diff Summary (What the Fix Changes)

### `src/lightning/pytorch/trainer/connectors/callback_connector.py`
```diff
@@ -240,7 +240,7 @@ def _reorder_callbacks(callbacks: list[Callback]) -> list[Callback]:
 
 
 def _validate_callbacks_list(callbacks: list[Callback]) -> None:
-    stateful_callbacks = [cb for cb in callbacks if is_overridden("state_dict", instance=cb)]
+    stateful_callbacks = [cb for cb in callbacks if is_overridden("state_dict", instance=cb, parent=Callback)]
     seen_callbacks = set()
     for callback in stateful_callbacks:
         if callback.state_key in seen_callbacks:
```

## Moved from `brief.md`

## Files That May Need Changes

- `src/lightning/pytorch/trainer/connectors/callback_connector.py`
