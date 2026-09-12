# Reference solution — GH861_pytorch_lightni_21224

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH861_pytorch_lightni_21224`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH861_pytorch_lightni_21224/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `src/lightning/pytorch/CHANGELOG.md` (modified, +3/-0)
- `src/lightning/pytorch/callbacks/finetuning.py` (modified, +8/-6)
- `tests/tests_pytorch/tuner/test_lr_finder.py` (modified, +45/-0)

## Diff Summary (What the Fix Changes)

### `src/lightning/pytorch/callbacks/finetuning.py`
```diff
@@ -108,12 +108,14 @@ def load_state_dict(self, state_dict: dict[str, Any]) -> None:
     def on_fit_start(self, trainer: "pl.Trainer", pl_module: "pl.LightningModule") -> None:
         # restore the param_groups created during the previous training.
         if self._restarting:
-            named_parameters = dict(pl_module.named_parameters())
-            for opt_idx, optimizer in enumerate(trainer.optimizers):
-                param_groups = self._apply_mapping_to_param_groups(
-                    self._internal_optimizer_metadata[opt_idx], named_parameters
-                )
-                optimizer.param_groups = param_groups
+            if self._internal_optimizer_metadata:
+                named_parameters = dict(pl_module.named_parameters())
+                for opt_idx, optimizer in enumerate(trainer.optimizers):
+                    if opt_idx in self._internal_optimizer_metadata:
+                        param_groups = self._apply_mapping_to_param_groups(
+                            self._internal_optimizer_metadata[opt_idx], named_parameters
+                        )
+                        optimizer.param_groups = param_groups
             self._restarting = False
 
     @staticmethod
```

## Moved from `brief.md`

## Files That May Need Changes

- `src/lightning/pytorch/callbacks/finetuning.py`
