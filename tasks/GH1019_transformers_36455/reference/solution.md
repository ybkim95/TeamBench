# Reference solution — GH1019_transformers_36455

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1019_transformers_36455`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1019_transformers_36455/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `src/transformers/integrations/deepspeed.py` (modified, +52/-0)
- `src/transformers/modeling_utils.py` (modified, +14/-2)
- `tests/deepspeed/test_deepspeed.py` (modified, +39/-1)

## Diff Summary (What the Fix Changes)

### `src/transformers/integrations/deepspeed.py`
```diff
@@ -27,6 +27,7 @@
 
 if is_torch_available():
     import torch
+    from torch import nn
 
 
 logger = logging.get_logger(__name__)
@@ -305,6 +306,57 @@ def deepspeed_config():
         return None
 
 
+def _load_state_dict_into_zero3_model(model_to_load, state_dict, start_prefix, assign_to_params_buffers=False):
+    """
+    Loads state dict into a model specifically for Zero3, since DeepSpeed does not support the `transformers`
+    tensor parallelism API.
+
+    Nearly identical code to PyTorch's `_load_from_state_dict`
+    """
+    # copy state_dict so `_load_state_dict_into_zero3_model` can modify it
+    metadata = getattr(state_dict, "_metadata", None)
+    state_dict = state_dict.copy()
+    if metadata is not None:
+        state_dict._metadata = metadata
+
+    error_msgs = []
+
+    # PyTorch's `_load_from_state_dict` does not copy parameters in a module's descendants
+    # so we need to apply the function recursively.
+    def load(module: nn.Module, state_dict, prefix="", assign_to_params_buffers=False):
+        local_metadata = {} if metadata is None else metadata.get(prefix[:-1], {})
+        local_metadata["assign_to_params_buffers"] = assign_to_params_buffers
+
+        args = (state_dict, prefix, local_metadata, True, [], [], error_msgs)
+        # Parameters of module and children will start with prefix. We can exit early if there are none in this
+        # state_dict
+        if is_deepspeed_zero3_enabled() and len([key for key in state_dict if key.startswith(prefix)]) > 0:
+            import deepspeed
+
+            # In sharded models, each shard has only part of the full state_dict, so only gather
+            # parameters that are in the current state_dict.
+            named_parameters = dict(module.named_parameters(prefix=prefix[:-1], recurse=False))
+            params_to_gather = [named_parameters[k] for k in state_dict.keys() if k in named_parameters]
+            if len(params_to_gather) > 0:
+                # because zero3 puts
```

### `src/transformers/modeling_utils.py`
```diff
@@ -50,6 +50,7 @@
 from .dynamic_module_utils import custom_object_save
 from .generation import CompileConfig, GenerationConfig, GenerationMixin
 from .integrations import PeftAdapterMixin, deepspeed_config, is_deepspeed_zero3_enabled
+from .integrations.deepspeed import _load_state_dict_into_zero3_model
 from .integrations.flash_attention import flash_attention_forward
 from .integrations.flex_attention import flex_attention_forward
 from .integrations.sdpa_attention import sdpa_attention_forward
@@ -4918,7 +4919,13 @@ def _load_pretrained_model(
                 mismatched_names = [name for name, _, _ in mismatched_keys]
                 fixed_state_dict = {k: v for k, v in state_dict.items() if k not in mismatched_names}
                 fixed_state_dict = model_to_load._fix_state_dict_keys_on_load(fixed_state_dict)
-                model_to_load.load_state_dict(fixed_state_dict, strict=False, assign=assign_to_params_buffers)
+
+                if is_deepspeed_zero3_enabled():
+                    error_msgs += _load_state_dict_into_zero3_model(
+                        model_to_load, fixed_state_dict, start_prefix, assign_to_params_buffers
+                    )
+                else:
+                    model_to_load.load_state_dict(fixed_state_dict, strict=False, assign=assign_to_params_buffers)
         else:
             # This should always be a list but, just to be sure.
             if not isinstance(resolved_archive_file, list):
@@ -5009,7 +5016,12 @@ def _load_pretrained_model(
                             model_to_load, state_dict, start_prefix
                         )
                     fixed_state_dict = model_to_load._fix_state_dict_keys_on_load(state_dict)
-                    model_to_load.load_state_dict(fixed_state_dict, strict=False, assign=assign_to_params_buffers)
+                    if is_deepspeed_zero3_enabled():
+                        error_msgs += _load_state_dict_into_zero3_model(
+                            model_to_load, fix
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `src/transformers/integrations/deepspeed.py`
- `src/transformers/modeling_utils.py`
