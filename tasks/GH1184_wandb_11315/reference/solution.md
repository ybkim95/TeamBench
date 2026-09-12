# Reference solution — GH1184_wandb_11315

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1184_wandb_11315`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1184_wandb_11315/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `tests/unit_tests/test_launch/test_runner/test_local_container.py` (modified, +110/-4)
- `wandb/sdk/launch/runner/local_container.py` (modified, +15/-1)

## Diff Summary (What the Fix Changes)

### `wandb/sdk/launch/runner/local_container.py`
```diff
@@ -4,6 +4,7 @@
 import logging
 import os
 import shlex
+import shutil
 import subprocess
 import sys
 import threading
@@ -203,13 +204,26 @@ def _run_entry_point(command: str, work_dir: str | None) -> AbstractRun:
     run = LocalSubmittedRun()
     thread = threading.Thread(
         target=_thread_process_runner,
-        args=(run, ["bash", "-c", command], work_dir, env),
+        args=(run, _shell_command(command), work_dir, env),
     )
     run.set_thread(thread)
     thread.start()
     return run
 
 
+def _shell_command(command: str) -> list[str]:
+    """Return a cross-platform shell invocation for command execution."""
+    if os.name == "nt":
+        return ["cmd", "/C", command]
+
+    shell = shutil.which("bash") or shutil.which("sh")
+    if shell is None:
+        raise LaunchError(
+            "Could not launch command: no compatible shell found (expected bash or sh)."
+        )
+    return [shell, "-c", command]
+
+
 def _thread_process_runner(
     run: LocalSubmittedRun, args: list[str], work_dir: str, env: dict[str, str]
 ) -> None:
```

## Moved from `brief.md`

## Files That May Need Changes

- `wandb/sdk/launch/runner/local_container.py`
