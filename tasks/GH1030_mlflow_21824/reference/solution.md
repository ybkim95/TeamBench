# Reference solution — GH1030_mlflow_21824

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1030_mlflow_21824`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1030_mlflow_21824/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `mlflow/pyfunc/dbconnect_artifact_cache.py` (modified, +15/-1)
- `mlflow/utils/file_utils.py` (modified, +37/-13)
- `tests/utils/test_file_utils.py` (modified, +124/-1)

## Diff Summary (What the Fix Changes)

### `mlflow/pyfunc/dbconnect_artifact_cache.py`
```diff
@@ -2,7 +2,9 @@
 import os
 import subprocess
 import tarfile
+from pathlib import Path
 
+from mlflow.exceptions import MlflowException
 from mlflow.utils.databricks_utils import is_in_databricks_runtime
 from mlflow.utils.file_utils import check_tarfile_security, get_or_create_tmp_dir
 
@@ -141,5 +143,17 @@ def extract_archive_to_dir(archive_path, dest_dir):
     check_tarfile_security(archive_path)
     os.makedirs(dest_dir, exist_ok=True)
     with tarfile.open(archive_path, "r") as tar:
-        tar.extractall(path=dest_dir)
+        _safe_extractall(tar, dest_dir)
     return dest_dir
+
+
+def _safe_extractall(tar, dest_dir):
+    resolved_dest = Path(dest_dir).resolve()
+    for member in tar.getmembers():
+        member_path = (resolved_dest / member.name).resolve()
+        if not (member_path == resolved_dest or resolved_dest in member_path.parents):
+            raise MlflowException.invalid_parameter_value(
+                f"Tar archive member {member.name!r} would be extracted outside "
+                f"the destination directory."
+            )
+        tar.extract(member, path=resolved_dest)
```

### `mlflow/utils/file_utils.py`
```diff
@@ -935,28 +935,52 @@ def check_tarfile_security(archive_path: str) -> None:
             # Normalize backslashes to forward slashes before path validation to prevent
             # bypass on Windows where backslashes are treated as directory separators.
             path = posixpath.normpath(m.name.replace("\\", "/"))
+            _check_path_is_safe(path)
             if m.issym():
                 symlink_set.add(path)
-            else:
-                if path.startswith("/"):
-                    raise MlflowException(
-                        "Absolute path destination in the archive file is not allowed, "
-                        f"but got path {path}."
-                    )
-                path_parts = path.split("/")
-                if path_parts[0] == "..":
-                    raise MlflowException(
-                        "Escaped path destination in the archive file is not allowed, "
-                        f"but got path {path}."
+            elif m.islnk():
+                symlink_set.add(path)
+                # Hard link targets are dangerous: tar.extract creates an actual hard
+                # link to the target path, so validate they don't escape.
+                link_target = posixpath.normpath(m.linkname.replace("\\", "/"))
+                _check_path_is_safe(link_target, context=f"hard link target of {path}")
+                link_parent = posixpath.dirname(path)
+                resolved = posixpath.normpath(posixpath.join(link_parent, link_target))
+                if resolved == ".." or resolved.startswith("../"):
+                    raise MlflowException.invalid_parameter_value(
+                        "Hard link target that escapes the extraction directory is not "
+                        f"allowed, but got {path} -> {link_target}."
                     )
         for m in tar.getmembers():
-            if not m.issym():
+            if not m.issym() and not m.islnk():
                 path = posixpath.normpath(m.name.replace
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `mlflow/pyfunc/dbconnect_artifact_cache.py`
- `mlflow/utils/file_utils.py`
