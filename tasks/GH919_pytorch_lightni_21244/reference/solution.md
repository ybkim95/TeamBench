# Reference solution — GH919_pytorch_lightni_21244

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH919_pytorch_lightni_21244`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH919_pytorch_lightni_21244/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `src/lightning/pytorch/CHANGELOG.md` (modified, +3/-0)
- `src/lightning/pytorch/callbacks/model_checkpoint.py` (modified, +10/-2)
- `tests/tests_pytorch/checkpointing/test_model_checkpoint.py` (modified, +57/-1)

## Diff Summary (What the Fix Changes)

### `src/lightning/pytorch/callbacks/model_checkpoint.py`
```diff
@@ -380,7 +380,11 @@ def on_train_epoch_end(self, trainer: "pl.Trainer", pl_module: "pl.LightningModu
             monitor_candidates = self._monitor_candidates(trainer)
             if self._every_n_epochs >= 1 and (trainer.current_epoch + 1) % self._every_n_epochs == 0:
                 self._save_topk_checkpoint(trainer, monitor_candidates)
-            self._save_last_checkpoint(trainer, monitor_candidates)
+            # Only save last checkpoint if a checkpoint was actually saved in this step or if save_last="link"
+            if self._last_global_step_saved == trainer.global_step or (
+                self.save_last == "link" and self._last_checkpoint_saved
+            ):
+                self._save_last_checkpoint(trainer, monitor_candidates)
 
     @override
     def on_validation_end(self, trainer: "pl.Trainer", pl_module: "pl.LightningModule") -> None:
@@ -397,7 +401,11 @@ def on_validation_end(self, trainer: "pl.Trainer", pl_module: "pl.LightningModul
 
             if self._every_n_epochs >= 1 and (trainer.current_epoch + 1) % self._every_n_epochs == 0:
                 self._save_topk_checkpoint(trainer, monitor_candidates)
-            self._save_last_checkpoint(trainer, monitor_candidates)
+            # Only save last checkpoint if a checkpoint was actually saved in this step or if save_last="link"
+            if self._last_global_step_saved == trainer.global_step or (
+                self.save_last == "link" and self._last_checkpoint_saved
+            ):
+                self._save_last_checkpoint(trainer, monitor_candidates)
 
     @override
     def on_exception(self, trainer: "pl.Trainer", pl_module: "pl.LightningModule", exception: BaseException) -> None:
```

## Moved from `brief.md`

## Files That May Need Changes

- `src/lightning/pytorch/callbacks/model_checkpoint.py`
