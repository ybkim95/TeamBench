# Reference solution — GH1077_spaCy_12623

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1077_spaCy_12623`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1077_spaCy_12623/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `spacy/tests/serialize/test_serialize_config.py` (modified, +50/-0)
- `spacy/tests/test_misc.py` (modified, +27/-0)
- `spacy/util.py` (modified, +20/-8)

## Diff Summary (What the Fix Changes)

### `spacy/util.py`
```diff
@@ -534,7 +534,7 @@ def load_model_from_path(
     if not meta:
         meta = get_model_meta(model_path)
     config_path = model_path / "config.cfg"
-    overrides = dict_to_dot(config)
+    overrides = dict_to_dot(config, for_overrides=True)
     config = load_config(config_path, overrides=overrides)
     nlp = load_model_from_config(
         config,
@@ -1502,14 +1502,19 @@ def dot_to_dict(values: Dict[str, Any]) -> Dict[str, dict]:
     return result
 
 
-def dict_to_dot(obj: Dict[str, dict]) -> Dict[str, Any]:
+def dict_to_dot(obj: Dict[str, dict], *, for_overrides: bool = False) -> Dict[str, Any]:
     """Convert dot notation to a dict. For example: {"token": {"pos": True,
     "_": {"xyz": True }}} becomes {"token.pos": True, "token._.xyz": True}.
 
-    values (Dict[str, dict]): The dict to convert.
+    obj (Dict[str, dict]): The dict to convert.
+    for_overrides (bool): Whether to enable special handling for registered
+        functions in overrides.
     RETURNS (Dict[str, Any]): The key/value pairs.
     """
-    return {".".join(key): value for key, value in walk_dict(obj)}
+    return {
+        ".".join(key): value
+        for key, value in walk_dict(obj, for_overrides=for_overrides)
+    }
 
 
 def dot_to_object(config: Config, section: str):
@@ -1551,13 +1556,20 @@ def set_dot_to_object(config: Config, section: str, value: Any) -> None:
 
 
 def walk_dict(
-    node: Dict[str, Any], parent: List[str] = []
+    node: Dict[str, Any], parent: List[str] = [], *, for_overrides: bool = False
 ) -> Iterator[Tuple[List[str], Any]]:
-    """Walk a dict and yield the path and values of the leaves."""
+    """Walk a dict and yield the path and values of the leaves.
+
+    for_overrides (bool): Whether to treat registered functions that start with
+        @ as final values rather than dicts to traverse.
+    """
     for key, value in node.items():
         key_parent = [*parent, key]
-        if isinstance(value, dict):
-            yield from walk_dict
```

## Moved from `brief.md`

## Files That May Need Changes

- `spacy/util.py`
