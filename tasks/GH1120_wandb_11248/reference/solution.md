# Reference solution — GH1120_wandb_11248

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1120_wandb_11248`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1120_wandb_11248/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `tests/unit_tests/test_public_api/test_public_api.py` (modified, +97/-43)
- `wandb/apis/public/api.py` (modified, +68/-26)

## Diff Summary (What the Fix Changes)

### `wandb/apis/public/api.py`
```diff
@@ -806,38 +806,80 @@ def _parse_project_path(self, path):
             return entity, path
         return parts
 
-    def _parse_path(self, path):
+    def _parse_path(self, path: str) -> tuple[str, str, str]:
         """Parse url, filepath, or docker paths.
 
         Allows paths in the following formats:
-        - url: entity/project/runs/id
-        - path: entity/project/id
-        - docker: entity/project:id
+        - entity/project/runs/id (URL)
+        - entity/project/id
+        - entity/project:id (Docker style)
+        - project/id
+        - project:id
+        - id (cannot contain colons)
 
-        Entity is optional and will fall back to the current logged-in user.
+        The path may also start with /runs/ or /sweeps/.
+
+        Returns:
+            A tuple with the extracted (entity, project, id).
+
+        Raises:
+            ValueError: If the path is in an invalid format or is missing
+                an entity that is not otherwise provided.
         """
-        project = self.settings["project"] or "uncategorized"
-        entity = self.settings["entity"] or self.default_entity
-        parts = (
-            path.replace("/runs/", "/").replace("/sweeps/", "/").strip("/ ").split("/")
-        )
-        if ":" in parts[-1]:
-            id = parts[-1].split(":")[-1]
-            parts[-1] = parts[-1].split(":")[0]
-        elif parts[-1]:
-            id = parts[-1]
-        if len(parts) == 1 and project != "uncategorized":
-            pass
-        elif len(parts) > 1:
-            project = parts[1]
-            if entity and id == project:
-                project = parts[0]
-            else:
-                entity = parts[0]
-            if len(parts) == 3:
+        # NOTE: This may result in a GQL call. Ideally we'd only access
+        # `self.default_entity` lazily, but changing this requires care as it
+        # changes when `self._default_entity` is cached and could impact other
+        # code.
+        entity: s
```

## Moved from `brief.md`

## Files That May Need Changes

- `wandb/apis/public/api.py`
