# Reference solution — GH1145_wandb_11237

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1145_wandb_11237`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1145_wandb_11237/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `tests/system_tests/test_notebooks/test_notebooks.py` (modified, +1/-1)
- `tests/unit_tests/test_library_public.py` (modified, +0/-1)
- `wandb/__init__.py` (modified, +1/-5)
- `wandb/jupyter.py` (modified, +12/-0)

## Diff Summary (What the Fix Changes)

### `wandb/__init__.py`
```diff
@@ -153,14 +153,10 @@ def set_trace():
     pdb.set_trace()
 
 
-def load_ipython_extension(ipython):
-    ipython.register_magics(wandb.jupyter.WandBMagics)
-
-
 if wandb_sdk.lib.ipython.in_notebook():
     from IPython import get_ipython  # type: ignore[import-not-found]
 
-    load_ipython_extension(get_ipython())
+    jupyter._load_ipython_extension(get_ipython())
 
 
 if "dev" in __version__:
```

### `wandb/jupyter.py`
```diff
@@ -491,3 +491,15 @@ def save_history(self, run: wandb.Run):
         except (OSError, validator.NotebookValidationError):
             wandb.termerror("Unable to save notebook session history.")
             logger.exception("Unable to save notebook session history.")
+
+
+def _load_ipython_extension(ipython):
+    """Best-effort auto-registration of W&B magics in notebook contexts."""
+    if ipython is None:
+        return
+
+    try:
+        ipython.register_magics(WandBMagics)
+    except Exception:
+        logger.debug("Failed to register IPython magics.", exc_info=True)
+        return
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `wandb/__init__.py`
- `wandb/jupyter.py`
