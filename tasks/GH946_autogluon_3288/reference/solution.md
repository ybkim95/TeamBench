# Reference solution — GH946_autogluon_3288

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH946_autogluon_3288`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH946_autogluon_3288/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `common/src/autogluon/common/utils/path_converter.py` (modified, +44/-3)
- `core/src/autogluon/core/models/abstract/abstract_model.py` (modified, +5/-0)
- `core/src/autogluon/core/models/ensemble/stacker_ensemble_model.py` (modified, +6/-0)
- `core/src/autogluon/core/trainer/abstract_trainer.py` (modified, +1/-0)
- `tabular/tests/conftest.py` (modified, +12/-2)
- `tabular/tests/unittests/models/test_dummy.py` (modified, +40/-0)

## Diff Summary (What the Fix Changes)

### `common/src/autogluon/common/utils/path_converter.py`
```diff
@@ -1,5 +1,6 @@
+import os
 import platform
-from pathlib import PurePosixPath, PureWindowsPath
+from pathlib import Path, PurePosixPath, PureWindowsPath
 
 
 class PathConverter:
@@ -20,13 +21,53 @@ def _validate_path(path: str):
     @staticmethod
     def to_windows(path: str) -> str:
         PathConverter._validate_path(path)
-        return str(PureWindowsPath(PurePosixPath(path)))
+        return str(PathConverter._to_windows(path))
+
+    @staticmethod
+    def _to_windows(path: str) -> PureWindowsPath:
+        return PureWindowsPath(PurePosixPath(path))
 
     @staticmethod
     def to_posix(path: str) -> str:
         PathConverter._validate_path(path)
-        return str(PurePosixPath(PureWindowsPath(path)))
+        return str(PathConverter._to_posix(path))
+
+    @staticmethod
+    def _to_posix(path: str) -> PurePosixPath:
+        return PurePosixPath(PureWindowsPath(path))
 
     @staticmethod
     def to_current(path: str) -> str:
         return PathConverter.to_windows(path) if PathConverter._is_windows() else PathConverter.to_posix(path)
+
+    @staticmethod
+    def os_path_sep() -> str:
+        return os.path.sep
+
+    # v0.9 FIXME: Avoid calling this as much as possible
+    #  Refactor code so that calling this is not necessary
+    @staticmethod
+    def to_relative(path: str) -> str:
+        if path == '':
+            return path
+        if not PathConverter._is_absolute(path=path):
+            return path
+        os_path_sep = PathConverter.os_path_sep()
+        path_relative = os.path.relpath(path)
+        if path.endswith(os_path_sep):
+            if not path_relative.endswith(os_path_sep):
+                path_relative += os_path_sep
+        return path_relative
+
+    @staticmethod
+    def to_absolute(path: str) -> str:
+        if path == '':
+            return path
+        if PathConverter._is_absolute(path=path):
+            return path
+        path_absolute = str(Path(path).resolve())
+        os_path_sep = PathCo
```

### `core/src/autogluon/core/models/abstract/abstract_model.py`
```diff
@@ -17,6 +17,7 @@
 from autogluon.common.features.feature_metadata import FeatureMetadata
 from autogluon.common.utils.try_import import try_import_ray
 from autogluon.common.utils.pandas_utils import get_approximate_df_mem_usage
+from autogluon.common.utils.path_converter import PathConverter
 from autogluon.common.utils.utils import setup_outputdir
 from autogluon.common.utils.lite import disable_if_lite_mode
 from autogluon.common.utils.log_utils import DuplicateFilter
@@ -112,6 +113,10 @@ def __init__(self,
             path_cur = setup_outputdir(path=None, create_dir=True, path_suffix=path_suffix)
             self.path_root = path_cur.rsplit(self.path_suffix, 1)[0]
             logger.log(20, f'Warning: No path was specified for model, defaulting to: {self.path_root}')
+
+        # v0.9 FIXME: This is a hack, change so we aren't vulnerable to self.path_root breaking things
+        self.path_root = PathConverter.to_relative(self.path_root)
+
         self.path = self.create_contexts(self.path_root + self.path_suffix)  # TODO: Make this path a function for consistency.
 
         self.num_classes = None
```

### `core/src/autogluon/core/models/ensemble/stacker_ensemble_model.py`
```diff
@@ -53,6 +53,12 @@ def __init__(self,
         self.base_model_names = base_model_names
         self.base_models_dict: Dict[str, AbstractModel] = base_models_dict  # String name -> Model objects
         self.base_model_paths_dict = base_model_paths_dict
+
+        # FIXME: DO NOT DO THIS, FIX ASAP
+        self.base_model_paths_dict = {
+            k: PathConverter.to_relative(v) for k, v in self.base_model_paths_dict.items()
+        }
+
         self.base_model_types_dict = base_model_types_dict
 
         # TODO: Consider deleting these variables after initialization
```

### `core/src/autogluon/core/trainer/abstract_trainer.py`
```diff
@@ -53,6 +53,7 @@ def __init__(self, path: str, problem_type: str, eval_metric=None,
                  num_classes=None, quantile_levels=None, low_memory=False, feature_metadata=None, k_fold=0, n_repeats=1,
                  sample_weight=None, weight_evaluation=False, save_data=False, random_state=0, verbosity=2):
         self.path = path
+        self.path = PathConverter.to_relative(self.path)
         self.problem_type = problem_type
         self.feature_metadata = feature_metadata
         self.save_data = save_data
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `common/src/autogluon/common/utils/path_converter.py`
- `core/src/autogluon/core/models/abstract/abstract_model.py`
- `core/src/autogluon/core/models/ensemble/stacker_ensemble_model.py`
- `core/src/autogluon/core/trainer/abstract_trainer.py`
