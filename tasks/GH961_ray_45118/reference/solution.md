# Reference solution — GH961_ray_45118

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH961_ray_45118`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH961_ray_45118/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `python/ray/serve/_private/autoscaling_state.py` (modified, +6/-5)
- `python/ray/serve/_private/deployment_state.py` (modified, +3/-1)
- `python/ray/serve/tests/test_controller_recovery.py` (modified, +11/-2)

## Diff Summary (What the Fix Changes)

### `python/ray/serve/_private/autoscaling_state.py`
```diff
@@ -100,10 +100,11 @@ def __init__(self, deployment_id: DeploymentID):
         self._target_capacity: Optional[float] = None
         self._target_capacity_direction: Optional[TargetCapacityDirection] = None
 
-    def register(
-        self, info: DeploymentInfo, curr_target_num_replicas: Optional[int] = None
-    ) -> int:
-        """Registers an autoscaling deployment's info."""
+    def register(self, info: DeploymentInfo, curr_target_num_replicas: int) -> int:
+        """Registers an autoscaling deployment's info.
+
+        Returns the number of replicas the target should be set to.
+        """
 
         config = info.deployment_config.autoscaling_config
         if (
@@ -331,7 +332,7 @@ def register_deployment(
         self,
         deployment_id: DeploymentID,
         info: DeploymentInfo,
-        curr_target_num_replicas: Optional[int] = None,
+        curr_target_num_replicas: int,
     ) -> int:
         """Register autoscaling deployment info."""
         assert info.deployment_config.autoscaling_config
```

### `python/ray/serve/_private/deployment_state.py`
```diff
@@ -1301,7 +1301,9 @@ def recover_target_state_from_checkpoint(
         )
         if self._target_state.info.deployment_config.autoscaling_config:
             self._autoscaling_state_manager.register_deployment(
-                self._id, self._target_state.info
+                self._id,
+                self._target_state.info,
+                self._target_state.target_num_replicas,
             )
 
     def recover_current_state_from_replica_actor_names(
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `python/ray/serve/_private/autoscaling_state.py`
- `python/ray/serve/_private/deployment_state.py`
