# Reference solution — GH989_great_expectati_8084

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH989_great_expectati_8084`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH989_great_expectati_8084/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `great_expectations/data_context/data_context/abstract_data_context.py` (modified, +32/-5)
- `great_expectations/data_context/data_context/cloud_data_context.py` (modified, +13/-3)
- `great_expectations/data_context/store/checkpoint_store.py` (modified, +19/-13)
- `great_expectations/data_context/store/gx_cloud_store_backend.py` (modified, +19/-0)
- `tests/data_context/cloud_data_context/test_checkpoint_crud.py` (modified, +206/-11)
- `tests/data_context/cloud_data_context/test_expectation_suite_crud.py` (modified, +1/-1)

## Diff Summary (What the Fix Changes)

### `great_expectations/data_context/data_context/abstract_data_context.py`
```diff
@@ -132,6 +132,7 @@
     send_usage_message,
     usage_statistics_enabled_method,
 )
+from great_expectations.checkpoint import Checkpoint
 
 SQLAlchemyError = sqlalchemy.SQLAlchemyError
 if not SQLAlchemyError:
@@ -143,7 +144,6 @@
 if TYPE_CHECKING:
     from typing_extensions import TypeAlias
 
-    from great_expectations.checkpoint import Checkpoint
     from great_expectations.checkpoint.configurator import ActionDict
     from great_expectations.checkpoint.types.checkpoint_result import CheckpointResult
     from great_expectations.core.expectation_configuration import (
@@ -1891,16 +1891,25 @@ def add_checkpoint(  # noqa: PLR0913
             checkpoint=checkpoint,
         )
 
+        result: Checkpoint | CheckpointConfig
         try:
-            return self.checkpoint_store.add_checkpoint(checkpoint)
+            result = self.checkpoint_store.add_checkpoint(checkpoint)
         except gx_exceptions.CheckpointError as e:
             # deprecated-v0.15.50
             warnings.warn(
                 f"{e.message}; using add_checkpoint to overwrite an existing value is deprecated as of v0.15.50 "
                 "and will be removed in v0.18. Please use add_or_update_checkpoint instead.",
                 DeprecationWarning,
             )
-            return self.checkpoint_store.add_or_update_checkpoint(checkpoint)
+            result = self.checkpoint_store.add_or_update_checkpoint(checkpoint)
+
+        if isinstance(result, CheckpointConfig):
+            result = Checkpoint.instantiate_from_config_with_runtime_args(
+                checkpoint_config=result,
+                data_context=self,
+                name=name,
+            )
+        return result
 
     @public_api
     @new_method_or_class(version="0.15.48")
@@ -1916,7 +1925,16 @@ def update_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint:
         Returns:
             The updated Checkpoint.
         """
-        return self.checkpoint_store.update_checkpoint(checkpoint)
+   
```

### `great_expectations/data_context/data_context/cloud_data_context.py`
```diff
@@ -19,6 +19,7 @@
 
 import great_expectations.exceptions as gx_exceptions
 from great_expectations import __version__
+from great_expectations.checkpoint.checkpoint import Checkpoint
 from great_expectations.core import ExpectationSuite
 from great_expectations.core._docs_decorators import public_api
 from great_expectations.core.config_provider import (
@@ -41,6 +42,7 @@
 )
 from great_expectations.data_context.types.base import (
     DEFAULT_USAGE_STATISTICS_URL,
+    CheckpointConfig,
     DataContextConfig,
     DataContextConfigDefaults,
     GXCloudConfig,
@@ -54,7 +56,6 @@
 
 if TYPE_CHECKING:
     from great_expectations.alias_types import PathStr
-    from great_expectations.checkpoint.checkpoint import Checkpoint
     from great_expectations.checkpoint.configurator import ActionDict
     from great_expectations.checkpoint.types.checkpoint_result import CheckpointResult
     from great_expectations.data_context.store.datasource_store import DatasourceStore
@@ -759,16 +760,25 @@ def add_checkpoint(  # noqa: PLR0913
             checkpoint=checkpoint,
         )
 
+        result: Checkpoint | CheckpointConfig
         try:
-            return self.checkpoint_store.add_checkpoint(checkpoint)
+            result = self.checkpoint_store.add_checkpoint(checkpoint)
         except gx_exceptions.CheckpointError as e:
             # deprecated-v0.16.16
             warnings.warn(
                 f"{e.message}; using add_checkpoint to overwrite an existing value is deprecated as of v0.16.16 "
                 "and will be removed in v0.18. Please use add_or_update_checkpoint instead.",
                 DeprecationWarning,
             )
-            return self.checkpoint_store.add_or_update_checkpoint(checkpoint)
+            result = self.checkpoint_store.add_or_update_checkpoint(checkpoint)
+
+        if isinstance(result, CheckpointConfig):
+            result = Checkpoint.instantiate_from_config_with_runtime_args(
+                checkpoint_config=result,
+
```

### `great_expectations/data_context/store/checkpoint_store.py`
```diff
@@ -155,7 +155,7 @@ def get_checkpoint(
 
         return checkpoint_config
 
-    def add_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint:
+    def add_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint | CheckpointConfig:
         """Persist a stand-alone Checkpoint object.
 
         Args:
@@ -177,7 +177,9 @@ def add_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint:
                 f"A Checkpoint named {checkpoint.name} already exists."
             )
 
-    def update_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint:
+    def update_checkpoint(
+        self, checkpoint: Checkpoint
+    ) -> Checkpoint | CheckpointConfig:
         """Use a stand-alone Checkpoint object to update a persisted value.
 
         Args:
@@ -199,7 +201,9 @@ def update_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint:
                 f"Could not find an existing Checkpoint named {checkpoint.name}."
             )
 
-    def add_or_update_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint:
+    def add_or_update_checkpoint(
+        self, checkpoint: Checkpoint
+    ) -> Checkpoint | CheckpointConfig:
         """Use a stand-alone Checkpoint object to either add or update a persisted value.
 
         Args:
@@ -227,18 +231,20 @@ def _persist_checkpoint(
         key: GXCloudIdentifier | ConfigurationIdentifier,
         checkpoint: Checkpoint,
         persistence_fn: Callable,
-    ) -> Checkpoint:
+    ) -> Checkpoint | CheckpointConfig:
         checkpoint_ref = persistence_fn(key=key, value=checkpoint.get_config())
         if isinstance(checkpoint_ref, GXCloudResourceRef):
-            # update parts of config that may have been updated by cloud (ids, default actions, etc.)
-            cloud_id = checkpoint_ref.id
-            checkpoint.config.ge_cloud_id = cloud_id
-            checkpoint.config.validations = checkpoint_ref.response["data"][
-                "attributes"
-            ]["checkpoint_config"].get("validations")
-            checkpo
```

### `great_expectations/data_context/store/gx_cloud_store_backend.py`
```diff
@@ -542,6 +542,25 @@ def remove_key(self, key):
                 f"Unable to delete object in GX Cloud Store Backend: {repr(e)}"
             )
 
+    def _update(self, key, value, **kwargs):
+        existing = self._get(key)
+        if key[1] is None:
+            key = (key[0], existing["data"]["id"], key[2])
+
+        return self.set(key=key, value=value, **kwargs)
+
+    def _add_or_update(self, key, value, **kwargs):
+        try:
+            existing = self._get(key)
+        except StoreBackendError as e:
+            logger.info(f"Could not find object associated with key {key}: {e}")
+            existing = None
+        if existing is not None:
+            id = key[1] if key[1] is not None else existing["data"]["id"]
+            key = (key[0], id, key[2])
+            return self.set(key=key, value=value, **kwargs)
+        return self.add(key=key, value=value, **kwargs)
+
     def _has_key(self, key: Tuple[str, ...]) -> bool:
         try:
             _ = self._get(key)
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `great_expectations/data_context/data_context/abstract_data_context.py`
- `great_expectations/data_context/data_context/cloud_data_context.py`
- `great_expectations/data_context/store/checkpoint_store.py`
- `great_expectations/data_context/store/gx_cloud_store_backend.py`
