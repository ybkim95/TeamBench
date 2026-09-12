# Reference solution — GH874_great_expectati_4042

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH874_great_expectati_4042`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH874_great_expectati_4042/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `great_expectations/datasource/data_connector/configured_asset_s3_data_connector.py` (modified, +21/-4)
- `great_expectations/datasource/data_connector/inferred_asset_s3_data_connector.py` (modified, +2/-4)
- `tests/datasource/data_connector/test_configured_asset_s3_data_connector.py` (modified, +33/-1)

## Diff Summary (What the Fix Changes)

### `great_expectations/datasource/data_connector/configured_asset_s3_data_connector.py`
```diff
@@ -13,9 +13,6 @@
 from great_expectations.datasource.data_connector.configured_asset_file_path_data_connector import (
     ConfiguredAssetFilePathDataConnector,
 )
-from great_expectations.datasource.data_connector.file_path_data_connector import (
-    FilePathDataConnector,
-)
 from great_expectations.datasource.data_connector.util import list_s3_keys
 from great_expectations.execution_engine import ExecutionEngine
 
@@ -82,7 +79,7 @@ def __init__(
             batch_spec_passthrough=batch_spec_passthrough,
         )
         self._bucket = bucket
-        self._prefix = FilePathDataConnector.sanitize_prefix(prefix)
+        self._prefix = self.sanitize_prefix_for_s3(prefix)
         self._delimiter = delimiter
         self._max_keys = max_keys
 
@@ -96,6 +93,26 @@ def __init__(
                 "Unable to load boto3 (it is required for ConfiguredAssetS3DataConnector)."
             )
 
+    @staticmethod
+    def sanitize_prefix_for_s3(text: str) -> str:
+        """
+        Takes in a given user-prefix and cleans it to work with file-system traversal methods
+        (i.e. add '/' to the end of a string meant to represent a directory)
+
+        Customized for S3 paths, ignoring the path separator used by the host OS
+        """
+        text = text.strip()
+        if not text:
+            return text
+
+        path_parts = text.split("/")
+        if not path_parts:  # Empty prefix
+            return text
+        elif "." in path_parts[-1]:  # File, not folder
+            return text
+        else:  # Folder, should have trailing /
+            return text.rstrip("/") + "/"
+
     def build_batch_spec(self, batch_definition: BatchDefinition) -> S3BatchSpec:
         """
         Build BatchSpec from batch_definition by calling DataConnector's build_batch_spec function.
```

### `great_expectations/datasource/data_connector/inferred_asset_s3_data_connector.py`
```diff
@@ -4,9 +4,7 @@
 import great_expectations.exceptions as ge_exceptions
 from great_expectations.core.batch import BatchDefinition
 from great_expectations.core.batch_spec import PathBatchSpec, S3BatchSpec
-from great_expectations.datasource.data_connector.file_path_data_connector import (
-    FilePathDataConnector,
-)
+from great_expectations.datasource.data_connector import ConfiguredAssetS3DataConnector
 
 try:
     import boto3
@@ -79,7 +77,7 @@ def __init__(
         )
 
         self._bucket = bucket
-        self._prefix = FilePathDataConnector.sanitize_prefix(prefix)
+        self._prefix = ConfiguredAssetS3DataConnector.sanitize_prefix_for_s3(prefix)
         self._delimiter = delimiter
         self._max_keys = max_keys
 
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `great_expectations/datasource/data_connector/configured_asset_s3_data_connector.py`
- `great_expectations/datasource/data_connector/inferred_asset_s3_data_connector.py`
