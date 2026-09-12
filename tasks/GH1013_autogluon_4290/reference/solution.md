# Reference solution — GH1013_autogluon_4290

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1013_autogluon_4290`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1013_autogluon_4290/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `common/src/autogluon/common/features/feature_metadata.py` (modified, +13/-0)
- `core/src/autogluon/core/models/abstract/abstract_model.py` (modified, +14/-3)
- `core/src/autogluon/core/models/ensemble/stacker_ensemble_model.py` (modified, +78/-30)
- `core/src/autogluon/core/trainer/abstract_trainer.py` (modified, +56/-16)
- `features/tests/features/test_feature_metadata.py` (modified, +27/-0)
- `tabular/tests/unittests/models/advanced/test_stack_feature_usage.py` (added, +145/-0)

## Diff Summary (What the Fix Changes)

### `common/src/autogluon/common/features/feature_metadata.py`
```diff
@@ -51,6 +51,19 @@ def __init__(self, type_map_raw: Dict[str, str], type_group_map_special: Dict[st
 
         self._validate()
 
+    def __eq__(self, other) -> bool:
+        if set(self.type_map_raw.keys()) != set(other.type_map_raw.keys()):
+            return False
+        for k in self.type_map_raw.keys():
+            if self.type_map_raw[k] != other.type_map_raw[k]:
+                return False
+        if set(self.type_group_map_special.keys()) != set(other.type_group_map_special.keys()):
+            return False
+        for k in self.type_group_map_special.keys():
+            if set(self.type_group_map_special[k]) != set(other.type_group_map_special[k]):
+                return False
+        return True
+
     # Confirms if inputs are valid
     def _validate(self):
         type_group_map_special_expanded = []
```

### `core/src/autogluon/core/models/abstract/abstract_model.py`
```diff
@@ -454,9 +454,10 @@ def _preprocess_set_features(self, X: pd.DataFrame, feature_metadata: FeatureMet
             self.features = list(X.columns)
         # TODO: Consider changing how this works or where it is done
         if feature_metadata is None:
-            feature_metadata = FeatureMetadata.from_df(X)
+            feature_metadata = self._infer_feature_metadata(X=X)
         else:
             feature_metadata = copy.deepcopy(feature_metadata)
+        feature_metadata = self._update_feature_metadata(X=X, feature_metadata=feature_metadata)
         get_features_kwargs = self.params_aux.get("get_features_kwargs", None)
         if get_features_kwargs is not None:
             valid_features = feature_metadata.get_features(**get_features_kwargs)
@@ -504,6 +505,16 @@ def _preprocess_set_features(self, X: pd.DataFrame, feature_metadata: FeatureMet
         if error_if_no_features and not self._features_internal:
             raise NoValidFeatures
 
+    def _update_feature_metadata(self, X: pd.DataFrame, feature_metadata: FeatureMetadata) -> FeatureMetadata:
+        """
+        [Advanced] Method that performs updates to feature_metadata during initialization.
+        Primarily present for use in stacker models.
+        """
+        return feature_metadata
+
+    def _infer_feature_metadata(self, X: pd.DataFrame) -> FeatureMetadata:
+        return FeatureMetadata.from_df(X)
+
     def _preprocess_fit_args(self, **kwargs) -> dict:
         sample_weight = kwargs.get("sample_weight", None)
         if sample_weight is not None and isinstance(sample_weight, str):
@@ -562,11 +573,11 @@ def _initialize(self, X=None, y=None, feature_metadata=None, num_classes=None, *
 
         self._init_misc(X=X, y=y, feature_metadata=feature_metadata, num_classes=num_classes, **kwargs)
 
+        self._init_params()
+
         if X is not None:
             self._preprocess_set_features(X=X, feature_metadata=feature_metadata)
 
-        self._init_params()
-
     def _init_m
```

### `core/src/autogluon/core/models/ensemble/stacker_ensemble_model.py`
```diff
@@ -1,16 +1,17 @@
+from __future__ import annotations
+
 import copy
 import logging
 import os
 import time
 from collections import defaultdict
-from typing import Dict
+from typing import Dict, List
 
 import numpy as np
 import pandas as pd
 
 from autogluon.common.features.feature_metadata import FeatureMetadata
 from autogluon.common.features.types import R_FLOAT, S_STACK
-from autogluon.common.utils.path_converter import PathConverter
 
 from ...constants import MULTICLASS, QUANTILE, SOFTCLASS
 from ..abstract.abstract_model import AbstractModel
@@ -35,12 +36,12 @@ class StackerEnsembleModel(BaggedEnsembleModel):
 
     def __init__(
         self,
-        base_model_names=None,
-        base_models_dict=None,
-        base_model_paths_dict=None,
-        base_model_types_dict=None,
-        base_model_types_inner_dict=None,
-        base_model_performances_dict=None,
+        base_model_names: List[str] | None = None,
+        base_models_dict: Dict[str, AbstractModel] | None = None,
+        base_model_paths_dict: Dict[str, str] = None,
+        base_model_types_dict: dict | None = None,
+        base_model_types_inner_dict: dict | None = None,
+        base_model_performances_dict: Dict[str, float] | None = None,
         **kwargs,
     ):
         super().__init__(**kwargs)
@@ -61,17 +62,22 @@ def __init__(
         self._base_model_performances_dict = base_model_performances_dict
         self._base_model_types_inner_dict = base_model_types_inner_dict
 
-    def _initialize(self, **kwargs):
-        super()._initialize(**kwargs)
+    def _update_feature_metadata(self, X: pd.DataFrame, feature_metadata: FeatureMetadata) -> FeatureMetadata:
+        """
+        Updates base_model_names and feature_metadata to reflect the used base models.
+        """
         base_model_performances_dict = self._base_model_performances_dict
         base_model_types_inner_dict = self._base_model_types_inner_dict
         if (base_model_performances_dict is not None) and
```

### `core/src/autogluon/core/trainer/abstract_trainer.py`
```diff
@@ -16,6 +16,7 @@
 import pandas as pd
 
 from autogluon.common.features.feature_metadata import FeatureMetadata
+from autogluon.common.features.types import R_FLOAT, S_STACK
 from autogluon.common.utils.lite import disable_if_lite_mode
 from autogluon.common.utils.log_utils import convert_time_in_s_to_log_friendly
 from autogluon.common.utils.path_converter import PathConverter
@@ -694,6 +695,8 @@ def stack_new_level_core(
                     "base_model_names": base_model_names,
                     "base_model_paths_dict": base_model_paths,
                     "base_model_types_dict": base_model_types,
+                    "base_model_types_inner_dict": self.get_models_attribute_dict(attribute="type_inner", models=base_model_names),
+                    "base_model_performances_dict": self.get_models_attribute_dict(attribute="val_score", models=base_model_names),
                     "random_state": level + self.random_state,
                 }
                 get_models_kwargs.update(
@@ -713,6 +716,7 @@ def stack_new_level_core(
                 kwargs["hyperparameter_tune_kwargs"] = hyperparameter_tune_kwargs
         logger.log(20, f"Fitting {len(models)} L{level} models ...")
         X_init = self.get_inputs_to_stacker(X, base_models=base_model_names, fit=True)
+        feature_metadata = self.get_feature_metadata(use_orig_features=True, base_models=base_model_names)
         if X_val is not None:
             X_val = self.get_inputs_to_stacker(X_val, base_models=base_model_names, fit=False, use_val_cache=True)
         compute_score = not refit_full
@@ -724,7 +728,10 @@ def stack_new_level_core(
         if X_unlabeled is not None:
             X_unlabeled = self.get_inputs_to_stacker(X_unlabeled, base_models=base_model_names, fit=False)
 
-        fit_kwargs = dict(num_classes=self.num_classes)
+        fit_kwargs = dict(
+            num_classes=self.num_classes,
+            feature_metadata=feature_metadata,
+        )
 
         # FIXME: TODO: v0.1
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `common/src/autogluon/common/features/feature_metadata.py`
- `core/src/autogluon/core/models/abstract/abstract_model.py`
- `core/src/autogluon/core/models/ensemble/stacker_ensemble_model.py`
- `core/src/autogluon/core/trainer/abstract_trainer.py`
