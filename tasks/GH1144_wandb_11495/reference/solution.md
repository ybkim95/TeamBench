# Reference solution — GH1144_wandb_11495

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1144_wandb_11495`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1144_wandb_11495/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `noxfile.py` (modified, +1/-1)
- `pyproject.toml` (modified, +0/-1)
- `requirements/requirements_dev.3.13.darwin.txt` (modified, +27/-32)
- `requirements/requirements_dev.3.13.linux.txt` (modified, +28/-33)
- `requirements/requirements_dev.3.13.windows.txt` (modified, +26/-31)
- `requirements/requirements_dev.3.9.darwin.txt` (modified, +19/-23)
- `requirements/requirements_dev.3.9.linux.txt` (modified, +19/-23)
- `requirements/requirements_dev.3.9.windows.txt` (modified, +18/-22)
- `requirements/requirements_dev.txt` (modified, +0/-1)
- `tests/system_tests/test_core/test_data_types_full.py` (modified, +5/-1)
- `wandb/sdk/data_types/bokeh.py` (modified, +15/-4)

## Diff Summary (What the Fix Changes)

### `noxfile.py`
```diff
@@ -82,7 +82,7 @@ def _requirements_file(python_version: str) -> str:
     Uses the current platform as the platform tag.
 
     Args:
-        python_version: Python version string, like "3.8", "3.9", "3.13".
+        python_version: Python version string, like "3.9", "3.13".
     """
     platform_tag = platform.system().lower()
 
```

### `wandb/sdk/data_types/bokeh.py`
```diff
@@ -18,6 +18,16 @@
     from bokeh import document, model
 
 
+def _doc_to_json(doc):
+    # Bokeh 3.9 returns Serialized[DocJson] from to_json() by default.
+    # Ask for plain JSON when supported; older Bokeh versions already
+    # return plain JSON and do not accept the 'deferred' kwarg.
+    try:
+        return doc.to_json(deferred=False)
+    except TypeError:
+        return doc.to_json()
+
+
 class Bokeh(Media):
     """Wandb class for Bokeh plots.
 
@@ -50,10 +60,11 @@ def __init__(
             _data.add_root(data_or_path)
             # serialize/deserialize pairing followed by sorting attributes ensures
             # that the file's sha's are equivalent in subsequent calls
-            self.b_obj = bokeh.document.Document.from_json(_data.to_json())
-            b_json = self.b_obj.to_json()
-            if "references" in b_json["roots"]:
-                b_json["roots"]["references"].sort(key=lambda x: x["id"])
+            self.b_obj = bokeh.document.Document.from_json(_doc_to_json(_data))
+            b_json = _doc_to_json(self.b_obj)
+            roots = b_json.get("roots")
+            if isinstance(roots, dict) and "references" in roots:
+                roots["references"].sort(key=lambda x: x["id"])
 
             tmp_path = os.path.join(MEDIA_TMP.name, runid.generate_id() + ".bokeh.json")
             with codecs.open(tmp_path, "w", encoding="utf-8") as fp:
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `noxfile.py`
- `wandb/sdk/data_types/bokeh.py`
