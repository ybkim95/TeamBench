# Reference solution — GH893_ray_23190

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH893_ray_23190`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH893_ray_23190/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `python/ray/workflow/storage/__init__.py` (modified, +9/-1)
- `python/ray/workflow/tests/test_basic_workflows.py` (modified, +16/-0)

## Diff Summary (What the Fix Changes)

### `python/ray/workflow/storage/__init__.py`
```diff
@@ -1,4 +1,5 @@
 import logging
+import os
 import urllib.parse as parse
 from ray.workflow.storage.base import Storage
 from ray.workflow.storage.base import DataLoadError, DataSaveError, KeyNotFoundError
@@ -48,7 +49,14 @@ def create_storage(storage_url: str) -> Storage:
         params = dict(parse.parse_qsl(parsed_url.query))
         return DebugStorage(create_storage(params["storage"]), path=parsed_url.path)
     else:
-        raise ValueError(f"Invalid url: {storage_url}")
+        extra_msg = ""
+        if os.name == "nt":
+            extra_msg = (
+                " Try using file://{} or file:///{} for Windows file paths.".format(
+                    storage_url, storage_url
+                )
+            )
+        raise ValueError(f"Invalid url: {storage_url}." + extra_msg)
 
 
 # the default storage is a local filesystem storage with a hidden directory
```

## Moved from `brief.md`

## Files That May Need Changes

- `python/ray/workflow/storage/__init__.py`
