# Reference solution — GH964_autogluon_2865

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH964_autogluon_2865`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH964_autogluon_2865/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `common/src/autogluon/common/utils/path_converter.py` (added, +32/-0)
- `common/tests/unittests/test_path_converter.py` (added, +57/-0)
- `core/src/autogluon/core/hpo/executors.py` (modified, +8/-0)
- `core/src/autogluon/core/models/abstract/abstract_model.py` (modified, +2/-4)
- `core/src/autogluon/core/models/ensemble/bagged_ensemble_model.py` (modified, +1/-2)
- `core/src/autogluon/core/models/ensemble/stacker_ensemble_model.py` (modified, +4/-0)
- `core/src/autogluon/core/trainer/abstract_trainer.py` (modified, +3/-0)
- `tabular/src/autogluon/tabular/models/fastainn/tabular_nn_fastai.py` (modified, +11/-0)

## Diff Summary (What the Fix Changes)

### `common/src/autogluon/common/utils/path_converter.py`
```diff
@@ -0,0 +1,32 @@
+import platform
+from pathlib import PurePosixPath, PureWindowsPath
+
+
+class PathConverter:
+    """Util class to convert a given path to a path to the corresponding OS"""
+
+    @staticmethod
+    def _is_windows():
+        return platform.system() == "Windows"
+    
+    @staticmethod
+    def _is_absolute(path: str) -> bool:
+        return PureWindowsPath(path).is_absolute() or PurePosixPath(path).is_absolute()
+    
+    @staticmethod
+    def _validate_path(path: str):
+        assert not PathConverter._is_absolute(path), "It is ambiguous on how to convert an absolute path. Please provide a relative path instead"
+
+    @staticmethod
+    def to_windows(path: str) -> str:
+        PathConverter._validate_path(path)
+        return str(PureWindowsPath(PurePosixPath(path)))
+
+    @staticmethod
+    def to_posix(path: str) -> str:
+        PathConverter._validate_path(path)
+        return str(PurePosixPath(PureWindowsPath(path)))
+
+    @staticmethod
+    def to_current(path: str) -> str:
+        return PathConverter.to_windows(path) if PathConverter._is_windows() else PathConverter.to_posix(path)
```

### `core/src/autogluon/core/hpo/executors.py`
```diff
@@ -399,6 +399,8 @@ def execute(
             model_estimate_memory_usage: float,
             adapter_type: str,
             trainable_is_parallel: bool = False,
+            tune_config_kwargs: Optional[Dict[str, Any]] = None,
+            run_config_kwargs: Optional[Dict[str, Any]] = None
         ):
         """
         Execute ray hpo experiment
@@ -425,6 +427,10 @@ def execute(
             Valid values are ['tabular', 'timeseries', 'automm', 'automm_ray_lightning']
         trainable_is_parallel
             Whether the trainable itself will use ray to run parallel job or not.
+        tune_config_kwargs
+            Additional args being passed to tune.TuneConfig https://docs.ray.io/en/latest/ray-air/package-ref.html#ray.tune.tune_config.TuneConfig
+        run_config_kwargs
+            Additional args being passed to air.RunConfig https://docs.ray.io/en/latest/ray-air/package-ref.html#ray.air.config.RunConfig
         """
         from .ray_hpo import (
             run,
@@ -449,6 +455,8 @@ def execute(
             model_estimate_memory_usage=model_estimate_memory_usage,
             time_budget_s=self.time_limit,
             verbose=0,
+            tune_config_kwargs=tune_config_kwargs,
+            run_config_kwargs=run_config_kwargs
         )
         os.environ.pop('TUNE_DISABLE_AUTO_CALLBACK_LOGGERS', None)
         self.analysis = analysis
```

### `core/src/autogluon/core/models/abstract/abstract_model.py`
```diff
@@ -989,7 +989,7 @@ def save(self, path: str = None, verbose=True) -> str:
         """
         if path is None:
             path = self.path
-        file_path = path + self.model_file_name
+        file_path = os.path.join(path, self.model_file_name)
         _model = self.model
         if self.model is not None:
             if self._compiler is None:
@@ -1375,9 +1375,6 @@ def _hyperparameter_tune(self, X, y, X_val, y_val, hpo_executor, **kwargs):
         except EmptySearchSpace:
             return skip_hpo(self, X=X, y=y, X_val=X_val, y_val=y_val, **kwargs)
 
-        # Use absolute path here because ray tune will change the working directory
-        self.set_contexts(os.path.abspath(self.path) + os.path.sep)
-
         directory = self.path
         os.makedirs(directory, exist_ok=True)
         data_path = directory
@@ -1421,6 +1418,7 @@ def _hyperparameter_tune(self, X, y, X_val, y_val, hpo_executor, **kwargs):
             minimum_gpu_per_trial=minimum_resources.get('num_gpus', 0),
             model_estimate_memory_usage=model_estimate_memory_usage,
             adapter_type='tabular',
+            tune_config_kwargs={'chdir_to_trial_dir': False}
         )
 
         hpo_results = hpo_executor.get_hpo_results(
```

### `core/src/autogluon/core/models/ensemble/bagged_ensemble_model.py`
```diff
@@ -1137,8 +1137,6 @@ def _hyperparameter_tune(
         except EmptySearchSpace:
             return skip_hpo(X=X, y=y, X_val=X_val, y_val=y_val, **kwargs)
 
-        # Use absolute path here because ray tune will change the working directory
-        self.set_contexts(os.path.abspath(self.path) + os.path.sep)
         directory = self.path
         os.makedirs(directory, exist_ok=True)
         data_path = directory
@@ -1199,6 +1197,7 @@ def _hyperparameter_tune(
             model_estimate_memory_usage=None,  # Not needed as we've already calculated it above
             adapter_type='tabular',
             trainable_is_parallel=True,
+            tune_config_kwargs={'chdir_to_trial_dir': False}
         )
 
         hpo_results = hpo_executor.get_hpo_results(
```

### `core/src/autogluon/core/models/ensemble/stacker_ensemble_model.py`
```diff
@@ -11,6 +11,7 @@
 
 from autogluon.common.features.feature_metadata import FeatureMetadata
 from autogluon.common.features.types import R_FLOAT, S_STACK
+from autogluon.common.utils.path_converter import PathConverter
 
 from .bagged_ensemble_model import BaggedEnsembleModel
 from ..abstract.abstract_model import AbstractModel
@@ -155,7 +156,10 @@ def _fit(self,
 
     def set_contexts(self, path_context):
         path_root_orig = self.path_root
+        path_root_orig = PathConverter.to_current(path_root_orig)
+        self.path_root = path_root_orig
         abs_path_root_orig = os.path.abspath(path_root_orig) + os.path.sep
+        self.base_model_paths_dict = {model: PathConverter.to_current(model_path) for model, model_path in self.base_model_paths_dict.items()}
         super().set_contexts(path_context=path_context)
         for model, model_path in self.base_model_paths_dict.items():
             model_path = os.path.abspath(model_path) + os.path.sep
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `common/src/autogluon/common/utils/path_converter.py`
- `core/src/autogluon/core/hpo/executors.py`
- `core/src/autogluon/core/models/abstract/abstract_model.py`
- `core/src/autogluon/core/models/ensemble/bagged_ensemble_model.py`
- `core/src/autogluon/core/models/ensemble/stacker_ensemble_model.py`
