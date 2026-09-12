# Reference solution — GH1011_great_expectati_8062

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1011_great_expectati_8062`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1011_great_expectati_8062/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `great_expectations/data_context/data_context/cloud_data_context.py` (modified, +10/-9)
- `great_expectations/data_context/store/checkpoint_store.py` (modified, +8/-2)
- `pyproject.toml` (modified, +3/-0)
- `tests/data_context/cloud_data_context/test_checkpoint_crud.py` (modified, +138/-24)

## Diff Summary (What the Fix Changes)

### `great_expectations/data_context/data_context/cloud_data_context.py`
```diff
@@ -764,15 +764,16 @@ def add_checkpoint(  # noqa: PLR0913
             checkpoint=checkpoint,
         )
 
-        checkpoint_config = self.checkpoint_store.create(
-            checkpoint_config=checkpoint.config
-        )
-
-        from great_expectations.checkpoint.checkpoint import Checkpoint
-
-        return Checkpoint.instantiate_from_config_with_runtime_args(
-            checkpoint_config=checkpoint_config, data_context=self  # type: ignore[arg-type]
-        )
+        try:
+            return self.checkpoint_store.add_checkpoint(checkpoint)
+        except gx_exceptions.CheckpointError as e:
+            # deprecated-v0.16.16
+            warnings.warn(
+                f"{e.message}; using add_checkpoint to overwrite an existing value is deprecated as of v0.16.16 "
+                "and will be removed in v0.18. Please use add_or_update_checkpoint instead.",
+                DeprecationWarning,
+            )
+            return self.checkpoint_store.add_or_update_checkpoint(checkpoint)
 
     def list_checkpoints(self) -> Union[List[str], List[ConfigurationIdentifier]]:
         return self.checkpoint_store.list_checkpoints(ge_cloud_mode=True)
```

### `great_expectations/data_context/store/checkpoint_store.py`
```diff
@@ -19,7 +19,6 @@
     DataContextConfigDefaults,
 )
 from great_expectations.data_context.types.refs import (
-    GXCloudIDAwareRef,
     GXCloudResourceRef,
 )
 from great_expectations.data_context.types.resource_identifiers import (  # noqa: TCH001
@@ -251,9 +250,16 @@ def _persist_checkpoint(
         persistence_fn: Callable,
     ) -> Checkpoint:
         checkpoint_ref = persistence_fn(key=key, value=checkpoint.get_config())
-        if isinstance(checkpoint_ref, GXCloudIDAwareRef):
+        if isinstance(checkpoint_ref, GXCloudResourceRef):
+            # update parts of config that may have been updated by cloud (ids, default actions, etc.)
             cloud_id = checkpoint_ref.id
             checkpoint.config.ge_cloud_id = cloud_id
+            checkpoint.config.validations = checkpoint_ref.response["data"][
+                "attributes"
+            ]["checkpoint_config"].get("validations")
+            checkpoint.config.action_list = checkpoint_ref.response["data"][
+                "attributes"
+            ]["checkpoint_config"].get("action_list")
         return checkpoint
 
     @public_api
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `great_expectations/data_context/data_context/cloud_data_context.py`
- `great_expectations/data_context/store/checkpoint_store.py`
