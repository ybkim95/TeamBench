# Reference solution — GH929_mlflow_9690

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH929_mlflow_9690`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH929_mlflow_9690/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `mlflow/langchain/__init__.py` (modified, +3/-6)
- `tests/langchain/test_langchain_model_export.py` (modified, +4/-1)

## Diff Summary (What the Fix Changes)

### `mlflow/langchain/__init__.py`
```diff
@@ -17,6 +17,7 @@
 import os
 import shutil
 import types
+from importlib.util import find_spec
 from typing import Any, Dict, List, NamedTuple, Optional, Union
 
 import cloudpickle
@@ -131,13 +132,9 @@ def _get_map_of_special_chain_class_to_loader_arg():
     if version.parse(langchain.__version__) <= version.parse("0.0.246"):
         class_name_to_loader_arg["langchain.chains.SQLDatabaseChain"] = "database"
     else:
-        try:
-            import langchain.experimental
-
+        if find_spec("langchain_experimental"):
+            # Add this entry only if langchain_experimental is installed
             class_name_to_loader_arg["langchain_experimental.sql.SQLDatabaseChain"] = "database"
-        except ImportError:
-            # Users may not have langchain_experimental installed, which is completely normal
-            pass
 
     class_to_loader_arg = {
         _RetrieverChain: "retriever",
```

## Moved from `brief.md`

## Files That May Need Changes

- `mlflow/langchain/__init__.py`
