# Reference solution — GH1146_evaluate_336

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1146_evaluate_336`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1146_evaluate_336/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `src/evaluate/loading.py` (modified, +29/-11)
- `tests/test_load.py` (modified, +30/-1)

## Diff Summary (What the Fix Changes)

### `src/evaluate/loading.py`
```diff
@@ -541,7 +541,9 @@ def get_module(self) -> ImportableModule:
         # get most recent
 
         def _get_modification_time(module_hash):
-            return (Path(importable_directory_path) / module_hash / (self.name + ".py")).stat().st_mtime
+            return (
+                (Path(importable_directory_path) / module_hash / (self.name.split("--")[-1] + ".py")).stat().st_mtime
+            )
 
         hash = sorted(hashes, key=_get_modification_time)[-1]
         logger.warning(
@@ -550,7 +552,9 @@ def _get_modification_time(module_hash):
             f"couldn't be found locally at {self.name}, or remotely on the Hugging Face Hub."
         )
         # make the new module to be noticed by the import system
-        module_path = ".".join([os.path.basename(dynamic_modules_path), self.module_type, self.name, hash, self.name])
+        module_path = ".".join(
+            [os.path.basename(dynamic_modules_path), self.module_type, self.name, hash, self.name.split("--")[-1]]
+        )
         importlib.invalidate_caches()
         return ImportableModule(module_path, hash)
 
@@ -658,15 +662,29 @@ def evaluation_module_factory(
                     dynamic_modules_path=dynamic_modules_path,
                 ).get_module()
         except Exception as e1:  # noqa: all the attempts failed, before raising the error we should check if the module is already cached.
-            try:
-                return CachedEvaluationModuleFactory(path, dynamic_modules_path=dynamic_modules_path).get_module()
-            except Exception as e2:  # noqa: if it's not in the cache, then it doesn't exist.
-                if not isinstance(e1, (ConnectionError, FileNotFoundError)):
-                    raise e1 from None
-                raise FileNotFoundError(
-                    f"Couldn't find a module script at {relative_to_absolute_path(combined_path)}. "
-                    f"Module '{path}' doesn't exist on the Hugging Face Hub either."
-                ) from None
+    
```

## Moved from `brief.md`

## Files That May Need Changes

- `src/evaluate/loading.py`
