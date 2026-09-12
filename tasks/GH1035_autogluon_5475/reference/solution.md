# Reference solution — GH1035_autogluon_5475

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1035_autogluon_5475`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1035_autogluon_5475/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `timeseries/src/autogluon/timeseries/models/toto/hf_pretrained_model.py` (modified, +95/-13)
- `timeseries/src/autogluon/timeseries/models/toto/model.py` (modified, +16/-3)
- `timeseries/tests/conftest.py` (modified, +3/-2)
- `timeseries/tests/smoketests/test_all_models.py` (modified, +1/-0)

## Diff Summary (What the Fix Changes)

### `timeseries/src/autogluon/timeseries/models/toto/hf_pretrained_model.py`
```diff
@@ -1,4 +1,7 @@
+import json
 import logging
+import os
+from pathlib import Path
 
 from transformers import PretrainedConfig, PreTrainedModel
 
@@ -68,19 +71,18 @@ def __init__(self, config: TotoConfig):
             scale_factor_exponent=config.scale_factor_exponent,
             **getattr(config, "extra_kwargs", {}),
         )
-        self._register_load_state_dict_pre_hook(self._remap_state_dict_keys_hook)
         self.post_init()
 
-    def _remap_state_dict_keys_hook(
-        self, state_dict, prefix, local_metadata, strict, missing_keys, unexpected_keys, error_msgs
-    ):
+    @staticmethod
+    def _remap_state_dict_keys(state_dict):
         remap = {
             "mlp.0.w12.weight": "mlp.0.weight",
             "mlp.0.w12.bias": "mlp.0.bias",
             "mlp.0.w3.weight": "mlp.2.weight",
             "mlp.0.w3.bias": "mlp.2.bias",
         }
 
+        new_state = {}
         keys_to_remap = []
         for key in list(state_dict.keys()):
             for old, new in remap.items():
@@ -89,11 +91,81 @@ def _remap_state_dict_keys_hook(
                     keys_to_remap.append((key, new_key))
                     break
 
+        new_state = state_dict.copy()
         for old_key, new_key in keys_to_remap:
-            state_dict[new_key] = state_dict.pop(old_key)
+            new_state[new_key] = new_state.pop(old_key)
+
+        return new_state
 
     @classmethod
-    def from_pretrained(cls, model_name_or_path, config=None, torch_dtype=None, device_map=None, **kwargs):
+    def load_from_checkpoint(
+        cls,
+        checkpoint_path,
+        device_map: str = "cpu",
+        strict=True,
+        **model_kwargs,
+    ):
+        """
+        Custom checkpoint loading. Used to load a local
+        safetensors checkpoint with an optional config.json file.
+        """
+        import safetensors.torch as safetorch
+
+        if os.path.isdir(checkpoint_path):
+            safetensors_file = os.path.join(checkpoint_path, "model.safetensors")
```

### `timeseries/src/autogluon/timeseries/models/toto/model.py`
```diff
@@ -126,7 +126,7 @@ def load_forecaster(self):
 
         hyperparameters = self.get_hyperparameters()
         pretrained_model = TotoPretrainedModel.from_pretrained(
-            self.model_path,
+            model_id=self.model_path,
             config=TotoConfig.from_pretrained(self.model_path),
             device_map=hyperparameters["device"],
         )
@@ -147,9 +147,21 @@ def _get_default_hyperparameters(self) -> dict:
             "num_samples": 256,
             "device": "cuda",
             "context_length": 4096,
-            "compile_model": True,
+            "compile_model": False,
         }
 
+    def _get_sample_batch_size(self) -> int:
+        num_samples = self.get_hyperparameter("num_samples")
+        batch_size = num_samples
+        while batch_size > 32:
+            for factor in range(2, int(batch_size**0.5) + 1):
+                if batch_size % factor == 0:
+                    batch_size //= factor
+                    break
+            else:  # batch_size is prime
+                return batch_size
+        return batch_size
+
     @property
     def allowed_hyperparameters(self) -> list[str]:
         return super().allowed_hyperparameters + [
@@ -198,6 +210,7 @@ def _predict(
         dataset = TotoInferenceDataset(
             target_df=data.fill_missing_values("auto"),
             max_context_length=hyperparameters["context_length"],
+            target_column=self.target,
         )
         loader = TotoDataLoader(
             dataset,
@@ -214,7 +227,7 @@ def _predict(
                     masked_timeseries,
                     prediction_length=self.prediction_length,
                     num_samples=hyperparameters["num_samples"],
-                    samples_per_batch=32,
+                    samples_per_batch=self._get_sample_batch_size(),
                 )
 
                 batch_means.append(forecast.mean.cpu().numpy())
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `timeseries/src/autogluon/timeseries/models/toto/hf_pretrained_model.py`
- `timeseries/src/autogluon/timeseries/models/toto/model.py`
