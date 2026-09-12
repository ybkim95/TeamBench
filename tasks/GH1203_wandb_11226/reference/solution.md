# Reference solution — GH1203_wandb_11226

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1203_wandb_11226`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1203_wandb_11226/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CHANGELOG.unreleased.md` (modified, +4/-0)
- `tests/system_tests/test_sweep/test_sweep_scheduler.py` (modified, +40/-1)
- `tests/system_tests/test_sweep/test_wandb_agent.py` (modified, +15/-0)
- `tests/system_tests/test_sweep/test_wandb_agent_full.py` (modified, +24/-0)
- `tests/unit_tests/test_internal_api.py` (modified, +31/-0)
- `wandb/agents/pyagent.py` (modified, +9/-1)
- `wandb/cli/cli.py` (modified, +13/-7)
- `wandb/sdk/internal/internal_api.py` (modified, +16/-0)
- `wandb/sdk/launch/sweeps/__init__.py` (modified, +6/-0)
- `wandb/sdk/launch/sweeps/scheduler_sweep.py` (modified, +13/-5)
- `wandb/wandb_agent.py` (modified, +2/-0)

## Diff Summary (What the Fix Changes)

### `wandb/agents/pyagent.py`
```diff
@@ -16,6 +16,7 @@
 
 import wandb
 from wandb.apis import InternalApi
+from wandb.sdk.launch.sweeps import SweepNotFoundError
 from wandb.sdk.launch.sweeps import utils as sweep_utils
 from wandb.sdk.lib import config_util
 
@@ -164,7 +165,14 @@ def _heartbeat(self):
                 for run, status in self._run_status.items()
                 if status in (RunStatus.QUEUED, RunStatus.RUNNING)
             }
-            commands = self._api.agent_heartbeat(self._agent_id, {}, run_status)
+            try:
+                commands = self._api.agent_heartbeat(self._agent_id, {}, run_status)
+            except SweepNotFoundError:
+                wandb.termerror(
+                    "Sweep was deleted or agent was not found. Stopping sweep."
+                )
+                self._exit()
+                return
             if commands:
                 job = Job(commands[0])
                 logger.debug(f"Job received: {job}")
```

### `wandb/cli/cli.py`
```diff
@@ -35,6 +35,7 @@
 from wandb.sdk.launch import utils as launch_utils
 from wandb.sdk.launch._launch_add import _launch_add
 from wandb.sdk.launch.errors import ExecutionError, LaunchError
+from wandb.sdk.launch.sweeps import SweepNotFoundError
 from wandb.sdk.launch.sweeps import utils as sweep_utils
 from wandb.sdk.launch.sweeps.scheduler import Scheduler
 from wandb.sdk.lib import filesystem, settings_file
@@ -1758,13 +1759,18 @@ def agent(ctx, project, entity, count, forward_signals, sweep_id):
         api = _get_cling_api(reset=True)
 
     wandb.termlog("Starting wandb agent 🕵️")
-    wandb_agent.agent(
-        sweep_id,
-        entity=entity,
-        project=project,
-        count=count,
-        forward_signals=forward_signals,
-    )
+    try:
+        wandb_agent.agent(
+            sweep_id,
+            entity=entity,
+            project=project,
+            count=count,
+            forward_signals=forward_signals,
+        )
+    # TODO: handle other errors with correct exit codes
+    except SweepNotFoundError:
+        wandb.termerror("Sweep was deleted or agent was not found. Stopping agent.")
+        sys.exit(1)
 
     # you can send local commands like so:
     # agent_api.command({'type': 'run', 'program': 'train.py',
```

### `wandb/sdk/internal/internal_api.py`
```diff
@@ -3133,9 +3133,18 @@ def agent_heartbeat(
             agent_id (str): agent_id
             metrics (dict): system metrics
             run_states (dict): run_id: state mapping
+
         Returns:
             list of commands to execute.
+
+        Raises:
+            SweepNotFoundError: If the server returns a 404, indicating the
+                sweep was likely deleted.
         """
+        import requests
+
+        from wandb.sdk.launch.sweeps import SweepNotFoundError
+
         mutation = gql(
             """
         mutation Heartbeat(
@@ -3170,6 +3179,13 @@ def agent_heartbeat(
                 },
                 timeout=60,
             )
+        except requests.exceptions.HTTPError as e:
+            if e.response is not None and e.response.status_code == 404:
+                raise SweepNotFoundError(
+                    "Sweep not found. The sweep may have been deleted."
+                ) from e
+            logger.exception("Error communicating with W&B.")
+            return []
         except Exception:
             logger.exception("Error communicating with W&B.")
             return []
```

### `wandb/sdk/launch/sweeps/__init__.py`
```diff
@@ -8,6 +8,10 @@ class SchedulerError(Exception):
     """Raised when a known error occurs with wandb sweep scheduler."""
 
 
+class SweepNotFoundError(Exception):
+    """Raised when a sweep is not found, typically because it was deleted."""
+
+
 def _import_sweep_scheduler() -> Any:
     from .scheduler_sweep import SweepScheduler
 
@@ -34,4 +38,6 @@ def load_scheduler(scheduler_type: str) -> Any:
 
 __all__ = [
     "load_scheduler",
+    "SchedulerError",
+    "SweepNotFoundError",
 ]
```

### `wandb/sdk/launch/sweeps/scheduler_sweep.py`
```diff
@@ -5,6 +5,7 @@
 from typing import Any, Dict, List, Optional
 
 import wandb
+from wandb.sdk.launch.sweeps import SweepNotFoundError
 from wandb.sdk.launch.sweeps.scheduler import LOG_PREFIX, RunState, Scheduler, SweepRun
 
 _logger = logging.getLogger(__name__)
@@ -68,11 +69,18 @@ def _get_sweep_commands(self, worker_id: int) -> List[Dict[str, Any]]:
                 _run_states[run_id] = True
 
         _logger.debug(f"Sending states: \n{pf(_run_states)}\n")
-        commands: List[Dict[str, Any]] = self._api.agent_heartbeat(
-            agent_id=self._workers[worker_id].agent_id,
-            metrics={},
-            run_states=_run_states,
-        )
+        try:
+            commands: List[Dict[str, Any]] = self._api.agent_heartbeat(
+                agent_id=self._workers[worker_id].agent_id,
+                metrics={},
+                run_states=_run_states,
+            )
+        except SweepNotFoundError:
+            wandb.termerror(
+                f"{LOG_PREFIX}Sweep was deleted or agent was not found. Stopping sweep."
+            )
+            self.stop_sweep()
+            return []
         _logger.debug(f"AgentHeartbeat commands: \n{pf(commands)}\n")
 
         return commands
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `wandb/agents/pyagent.py`
- `wandb/cli/cli.py`
- `wandb/sdk/internal/internal_api.py`
- `wandb/sdk/launch/sweeps/__init__.py`
- `wandb/sdk/launch/sweeps/scheduler_sweep.py`
