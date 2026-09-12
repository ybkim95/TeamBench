# Reference solution — GH1129_gpytorch_2559

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1129_gpytorch_2559`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1129_gpytorch_2559/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `gpytorch/models/exact_prediction_strategies.py` (modified, +1/-1)
- `gpytorch/priors/prior.py` (modified, +25/-0)
- `gpytorch/priors/torch_priors.py` (modified, +3/-0)
- `gpytorch/priors/utils.py` (modified, +29/-4)
- `test/priors/test_prior.py` (added, +70/-0)
- `test/priors/test_utils.py` (added, +61/-0)

## Diff Summary (What the Fix Changes)

### `gpytorch/models/exact_prediction_strategies.py`
```diff
@@ -865,5 +865,5 @@ def exact_predictive_covar(self, test_test_covar, test_train_covar):
                 "This is likely a bug in GPyTorch."
             )
 
-        res = test_test_covar - (L @ (covar_cache @ L.transpose(-1, -2)))
+        res = test_test_covar - MatmulLinearOperator(L, covar_cache @ L.mT)
         return res
```

### `gpytorch/priors/prior.py`
```diff
@@ -1,10 +1,18 @@
 #!/usr/bin/env python3
 
 from abc import ABC
+from typing import Any, Mapping
 
+from torch.distributions import TransformedDistribution
 from torch.nn import Module
 
 from ..distributions import Distribution
+from .utils import _load_transformed_to_base_dist
+
+
+TRANSFORMED_ERROR_MSG = """Priors of TransformedDistributions should not have their \
+'_transformed' attributes modified, these are just copies of the base attribute. \
+Please modify the base attribute (e.g. {}) instead."""
 
 
 class Prior(Distribution, Module, ABC):
@@ -25,3 +33,20 @@ def log_prob(self, x):
         :rtype: torch.Tensor
         """
         return super(Prior, self).log_prob(self.transform(x))
+
+    def load_state_dict(self, state_dict: Mapping[str, Any], *args, **kwargs):
+        Module.load_state_dict(self, state_dict, *args, **kwargs)
+        if isinstance(self, TransformedDistribution):
+            _load_transformed_to_base_dist(self)
+
+    def __setattr__(self, name: str, value: Any) -> None:
+        if hasattr(self, name) and "_transformed_" in name:
+            base_attr_name = name.replace("_transformed_", "")
+            raise AttributeError(TRANSFORMED_ERROR_MSG.format(base_attr_name))
+
+        elif hasattr(self, f"_transformed_{name}"):
+            self.base_dist.__setattr__(name, value)
+            super().__setattr__(f"_transformed_{name}", value)
+
+        else:
+            return super().__setattr__(name, value)
```

### `gpytorch/priors/torch_priors.py`
```diff
@@ -40,6 +40,7 @@ class HalfNormalPrior(Prior, HalfNormal):
     def __init__(self, scale, validate_args=None, transform=None):
         TModule.__init__(self)
         HalfNormal.__init__(self, scale=scale, validate_args=validate_args)
+        _bufferize_attributes(self, ("scale",))
         self._transform = transform
 
     def expand(self, batch_shape):
@@ -54,6 +55,7 @@ class LogNormalPrior(Prior, LogNormal):
     def __init__(self, loc, scale, validate_args=None, transform=None):
         TModule.__init__(self)
         LogNormal.__init__(self, loc=loc, scale=scale, validate_args=validate_args)
+        _bufferize_attributes(self, ("loc", "scale"))
         self._transform = transform
 
     def expand(self, batch_shape):
@@ -84,6 +86,7 @@ class HalfCauchyPrior(Prior, HalfCauchy):
     def __init__(self, scale, validate_args=None, transform=None):
         TModule.__init__(self)
         HalfCauchy.__init__(self, scale=scale, validate_args=validate_args)
+        _bufferize_attributes(self, ("scale",))
         self._transform = transform
 
     def expand(self, batch_shape):
```

### `gpytorch/priors/utils.py`
```diff
@@ -1,11 +1,36 @@
 #!/usr/bin/env python3
 
+from torch.distributions import TransformedDistribution
+
 
 def _bufferize_attributes(module, attributes):
-    attr_clones = {attr: getattr(module, attr).clone() for attr in attributes}
-    for attr, value in attr_clones.items():
-        delattr(module, attr)
-        module.register_buffer(attr, value)
+    r"""
+    Adds the parameters of the prior as a torch buffer to enable saving/
+    loading to/from state_dicts.
+    For TransformedDistributions Adds a _transformed_ attribute to the
+    parameters. This enables its parameters to be saved and
+    loaded to/from state_dicts, as the original parameters cannot be.
+    """
+    if isinstance(module, TransformedDistribution):
+        for attr in attributes:
+            module.register_buffer(f"_transformed_{attr}", getattr(module, attr))
+    else:
+        attr_clones = {attr: getattr(module, attr).clone() for attr in attributes}
+        for attr, value in attr_clones.items():
+            delattr(module, attr)
+            module.register_buffer(attr, value)
+
+
+def _load_transformed_to_base_dist(module):
+    r"""loads the  _transformed_ attributes to the parameters of a torch
+    TransformedDistribution. This enables its parameters to be saved and
+    loaded to/from state_dicts, as the original parameters cannot be.
+    """
+    transf_str = "_transformed_"
+    transformed_attrs = [attr for attr in dir(module) if transf_str in attr]
+    for transf_attr in transformed_attrs:
+        base_attr_name = transf_attr.replace(transf_str, "")
+        setattr(module.base_dist, base_attr_name, getattr(module, transf_attr))
 
 
 def _del_attributes(module, attributes, raise_on_error=False):
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `gpytorch/models/exact_prediction_strategies.py`
- `gpytorch/priors/prior.py`
- `gpytorch/priors/torch_priors.py`
- `gpytorch/priors/utils.py`
