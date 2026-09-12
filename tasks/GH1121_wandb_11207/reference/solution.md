# Reference solution — GH1121_wandb_11207

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1121_wandb_11207`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1121_wandb_11207/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CHANGELOG.unreleased.md` (modified, +9/-0)
- `tests/fixtures/mock_wandb_log.py` (modified, +32/-9)
- `tests/unit_tests/test_wandb_settings.py` (modified, +93/-0)
- `wandb/_pydantic/__init__.py` (modified, +4/-0)
- `wandb/sdk/wandb_settings.py` (modified, +88/-24)

## Diff Summary (What the Fix Changes)

### `wandb/_pydantic/__init__.py`
```diff
@@ -22,8 +22,12 @@
     "to_json",
     "from_json",
     "gql_typename",
+    "ValidationError",
 ]
 
+# Available in all supported Pydantic versions.
+from pydantic import ValidationError
+
 from .base import CompatBaseModel, GQLBase, GQLInput, GQLResult, JsonableModel
 from .field_types import GQLId, Typename
 from .pagination import Connection, ConnectionWithTotal, Edge, PageInfo
```

### `wandb/sdk/wandb_settings.py`
```diff
@@ -9,6 +9,7 @@
 import shutil
 import socket
 import sys
+import traceback
 from datetime import datetime
 
 # Optional and Union are used for type hinting instead of | because
@@ -27,6 +28,7 @@
 from wandb._pydantic import (
     IS_PYDANTIC_V2,
     AliasChoices,
+    ValidationError,
     computed_field,
     field_validator,
     model_validator,
@@ -1799,38 +1801,54 @@ def read_system_settings(self) -> settings_file.SettingsFiles:
     def update_from_system_settings(self) -> None:
         """Load settings from the settings files.
 
+        If settings files contain invalid settings, prints and suppresses
+        the error.
+
         <!-- lazydoc-ignore: internal -->
         """
         system_settings = self.read_system_settings()
 
-        if not self.quiet and (sources := system_settings.sources):
-            parts = ["Loaded settings from"]
-            for source in sources:
-                parts.append(f"  {source}")
-            wandb.termlog("\n".join(parts))
+        if len(system_settings.sources) == 0:
+            return
+        elif len(system_settings.sources) == 1:
+            source_string = str(system_settings.sources[0])
+        else:
+            source_string = "\n" + "\n".join(
+                f"  {source}" for source in system_settings.sources
+            )
 
-        value: object  # Can be transformed arbitrarily.
-        for key, value in system_settings.all().items():
-            if key == "ignore_globs":
-                value = value.split(",")
+        # Print at the start so that users can diagnose uncaught exceptions.
+        if not self.quiet:
+            printed_sources = True
+            wandb.termlog(f"Loading settings from {source_string}")
+        else:
+            printed_sources = False
 
-            elif key == "anonymous":
-                wandb.termwarn(
-                    "Deprecated setting 'anonymous' has no effect and will be"
-                    + " removed in a future version of wandb."
-
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `wandb/_pydantic/__init__.py`
- `wandb/sdk/wandb_settings.py`
