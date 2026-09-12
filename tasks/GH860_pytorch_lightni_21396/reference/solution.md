# Reference solution — GH860_pytorch_lightni_21396

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH860_pytorch_lightni_21396`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH860_pytorch_lightni_21396/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `src/lightning/pytorch/CHANGELOG.md` (modified, +3/-0)
- `src/lightning/pytorch/callbacks/stochastic_weight_avg.py` (modified, +14/-7)
- `tests/tests_pytorch/callbacks/test_stochastic_weight_avg.py` (modified, +30/-0)

## Diff Summary (What the Fix Changes)

### `src/lightning/pytorch/callbacks/stochastic_weight_avg.py`
```diff
@@ -139,6 +139,8 @@ def swa_start(self) -> int:
 
     @property
     def swa_end(self) -> int:
+        if self._max_epochs == -1:
+            return float("inf")  # type: ignore[return-value]
         return self._max_epochs - 1  # 0-based
 
     @staticmethod
@@ -163,12 +165,17 @@ def on_fit_start(self, trainer: "pl.Trainer", pl_module: "pl.LightningModule") -
 
         assert trainer.max_epochs is not None
         if isinstance(self._swa_epoch_start, float):
+            if trainer.max_epochs == -1:
+                raise MisconfigurationException(
+                    "SWA with `swa_epoch_start` as a float is not supported when `max_epochs=-1`. "
+                    "Please provide `swa_epoch_start` as an integer."
+                )
             self._swa_epoch_start = int(trainer.max_epochs * self._swa_epoch_start)
 
         self._model_contains_batch_norm = self.pl_module_contains_batch_norm(pl_module)
 
         self._max_epochs = trainer.max_epochs
-        if self._model_contains_batch_norm:
+        if self._model_contains_batch_norm and trainer.max_epochs != -1:
             # virtually increase max_epochs to perform batch norm update on latest epoch.
             assert trainer.fit_loop.max_epochs is not None
             trainer.fit_loop.max_epochs += 1
@@ -243,7 +250,7 @@ def on_train_epoch_start(self, trainer: "pl.Trainer", pl_module: "pl.LightningMo
             self._latest_update_epoch = trainer.current_epoch
 
         # Note: No > here in case the callback is saved with the model and training continues
-        if trainer.current_epoch == self.swa_end + 1:
+        if self._max_epochs != -1 and trainer.current_epoch == self.swa_end + 1:
             # Transfer weights from average model to pl_module
             assert self._average_model is not None
             self.transfer_weights(self._average_model, pl_module)
@@ -267,17 +274,17 @@ def on_train_epoch_end(self, trainer: "pl.Trainer", *args: Any) -> None:
     @override
     def on_tra
```

## Moved from `brief.md`

## Files That May Need Changes

- `src/lightning/pytorch/callbacks/stochastic_weight_avg.py`
