# Reference solution — GH1176_keras_21706

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1176_keras_21706`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1176_keras_21706/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `keras/src/optimizers/base_optimizer.py` (modified, +14/-0)
- `keras/src/optimizers/loss_scale_optimizer.py` (modified, +46/-13)
- `keras/src/optimizers/loss_scale_optimizer_test.py` (modified, +126/-13)

## Diff Summary (What the Fix Changes)

### `keras/src/optimizers/base_optimizer.py`
```diff
@@ -631,6 +631,20 @@ def _backend_increment_gradient_accumulators(self, grads, acc_grads):
             g_acc.assign(n_g_acc)
 
     def stateless_apply(self, optimizer_variables, grads, trainable_variables):
+        """Stateless version of `apply` that returns modified variables.
+
+        Args:
+            optimizer_variables: list of tensors containing the current values
+                for the optimizer variables. These are native tensors and not
+                `keras.Variable`s.
+            grads: list of gradients to apply.
+            trainable_variables: list of tensors containing the current values
+                for the model variables. These are native tensors and not
+                `keras.Variable`s.
+
+        Returns: A tuple containing two list of tensors, the updated
+            `trainable_variables` and the updated `optimizer_variables`.
+        """
         self._check_super_called()
 
         if not self.built:
```

### `keras/src/optimizers/loss_scale_optimizer.py`
```diff
@@ -48,6 +48,7 @@ def __init__(
         inner_optimizer,
         initial_scale=2.0**15,
         dynamic_growth_steps=2000,
+        name=None,
         **kwargs,
     ):
         if not kwargs.pop("dynamic", True):
@@ -56,7 +57,42 @@ def __init__(
                 "Instead, simply set `loss_scale_factor` directly on the "
                 "`inner_optimizer`."
             )
-        super().__init__(learning_rate=0.0, **kwargs)
+
+        # Backwards compatibility code for deserialization.
+        # LossScaleOptimizer used to return all these parameters in `get_config`
+        # from `super.get_config` even though they are all non-functional. We
+        # no longer let user set them, but we have to allow the default values
+        # to be passed during deserialization to support older models.
+        base_optimizer_defaults = {
+            "weight_decay": None,
+            "clipnorm": None,
+            "global_clipnorm": None,
+            "clipvalue": None,
+            "use_ema": False,
+            "ema_momentum": 0.99,
+            "ema_overwrite_frequency": None,
+            "loss_scale_factor": None,
+            "gradient_accumulation_steps": None,
+        }
+        for arg_name, default_value in base_optimizer_defaults.items():
+            if arg_name not in kwargs:
+                continue
+            arg_value = kwargs.pop(arg_name)
+            if (
+                default_value is None and arg_value is not None
+            ) or arg_value != default_value:
+                raise ValueError(
+                    f"LossScaleOptimizer does not support `{arg_name}`. "
+                    f"Instead, set `{arg_name}` on the `inner_optimizer`."
+                )
+
+        if kwargs:
+            raise ValueError(
+                "LossScaleOptimizer does not support arguments: "
+                f"`{'`, `'.join(kwargs.keys())}`."
+            )
+
+        super().__init__(learning_rate=0.0, name=name)
         self.inner_optimizer = inner_o
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `keras/src/optimizers/base_optimizer.py`
- `keras/src/optimizers/loss_scale_optimizer.py`
