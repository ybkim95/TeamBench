# Reference solution — GH1055_mlflow_1227

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1055_mlflow_1227`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1055_mlflow_1227/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `mlflow/tracking/artifact_utils.py` (modified, +11/-5)
- `tests/store/test_cli.py` (modified, +48/-0)

## Diff Summary (What the Fix Changes)

### `mlflow/tracking/artifact_utils.py`
```diff
@@ -53,8 +53,14 @@ def _download_artifact_from_uri(artifact_uri, output_path=None):
     :param output_path: The local filesystem path to which to download the artifact. If unspecified,
                         a local output path will be created.
     """
-    artifact_src_dir = posixpath.dirname(artifact_uri)
-    artifact_src_relative_path = posixpath.basename(artifact_uri)
-    artifact_repo = get_artifact_repository(artifact_uri=artifact_src_dir)
-    return artifact_repo.download_artifacts(artifact_path=artifact_src_relative_path,
-                                            dst_path=output_path)
+    parsed_uri = urllib.parse.urlparse(artifact_uri)
+    prefix = ""
+    if parsed_uri.scheme and not parsed_uri.path.startswith("/"):
+        # relative path is a special case, urllib does not reconstruct it properly
+        prefix = parsed_uri.scheme + ":"
+        parsed_uri = parsed_uri._replace(scheme="")
+    artifact_path = posixpath.basename(parsed_uri.path)
+    parsed_uri = parsed_uri._replace(path=posixpath.dirname(parsed_uri.path))
+    root_uri = prefix + urllib.parse.urlunparse(parsed_uri)
+    return get_artifact_repository(artifact_uri=root_uri).download_artifacts(
+        artifact_path=artifact_path, dst_path=output_path)
```

## Moved from `brief.md`

## Files That May Need Changes

- `mlflow/tracking/artifact_utils.py`
