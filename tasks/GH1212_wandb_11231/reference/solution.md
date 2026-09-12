# Reference solution — GH1212_wandb_11231

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1212_wandb_11231`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1212_wandb_11231/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CHANGELOG.unreleased.md` (modified, +3/-0)
- `tests/system_tests/test_core/test_offline_sync_beta.py` (modified, +7/-1)
- `wandb/cli/beta_sync.py` (modified, +10/-1)

## Diff Summary (What the Fix Changes)

### `wandb/cli/beta_sync.py`
```diff
@@ -13,7 +13,7 @@
 from wandb.errors import term
 from wandb.proto.wandb_sync_pb2 import ServerSyncResponse
 from wandb.sdk import wandb_setup
-from wandb.sdk.lib import asyncio_compat
+from wandb.sdk.lib import asyncio_compat, wbauth
 from wandb.sdk.lib.printer import Printer, new_printer
 from wandb.sdk.lib.progress import progress_printer
 from wandb.sdk.lib.service.service_connection import ServiceConnection
@@ -88,6 +88,15 @@ def sync(
     if ask_for_confirmation and not term.confirm("Sync the listed runs?"):
         return
 
+    # Authenticate the session. This updates the singleton settings credentials.
+    if not wbauth.authenticate_session(
+        host=singleton.settings.base_url,
+        source="wandb sync",
+        no_offline=True,
+    ):
+        term.termlog("Not authenticated.")
+        return
+
     service = singleton.ensure_service()
     printer = new_printer()
     singleton.asyncer.run(
```

## Moved from `brief.md`

## Files That May Need Changes

- `wandb/cli/beta_sync.py`
