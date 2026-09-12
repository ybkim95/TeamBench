# Reference solution — GH863_pytorch_lightni_21147

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH863_pytorch_lightni_21147`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH863_pytorch_lightni_21147/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `src/lightning/pytorch/CHANGELOG.md` (modified, +2/-0)
- `src/lightning/pytorch/callbacks/progress/tqdm_progress.py` (modified, +12/-4)
- `tests/tests_pytorch/callbacks/progress/test_tqdm_progress_bar.py` (modified, +47/-0)

## Diff Summary (What the Fix Changes)

### `src/lightning/pytorch/callbacks/progress/tqdm_progress.py`
```diff
@@ -265,7 +265,9 @@ def on_train_start(self, *_: Any) -> None:
     def on_train_epoch_start(self, trainer: "pl.Trainer", *_: Any) -> None:
         if self._leave:
             self.train_progress_bar = self.init_train_tqdm()
-        self.train_progress_bar.reset(convert_inf(self.total_train_batches))
+        total = convert_inf(self.total_train_batches)
+        self.train_progress_bar.reset()
+        self.train_progress_bar.total = total
         self.train_progress_bar.initial = 0
         self.train_progress_bar.set_description(f"Epoch {trainer.current_epoch}")
 
@@ -306,7 +308,9 @@ def on_validation_batch_start(
         if not self.has_dataloader_changed(dataloader_idx):
             return
 
-        self.val_progress_bar.reset(convert_inf(self.total_val_batches_current_dataloader))
+        total = convert_inf(self.total_val_batches_current_dataloader)
+        self.val_progress_bar.reset()
+        self.val_progress_bar.total = total
         self.val_progress_bar.initial = 0
         desc = self.sanity_check_description if trainer.sanity_checking else self.validation_description
         self.val_progress_bar.set_description(f"{desc} DataLoader {dataloader_idx}")
@@ -348,7 +352,9 @@ def on_test_batch_start(
         if not self.has_dataloader_changed(dataloader_idx):
             return
 
-        self.test_progress_bar.reset(convert_inf(self.total_test_batches_current_dataloader))
+        total = convert_inf(self.total_test_batches_current_dataloader)
+        self.test_progress_bar.reset()
+        self.test_progress_bar.total = total
         self.test_progress_bar.initial = 0
         self.test_progress_bar.set_description(f"{self.test_description} DataLoader {dataloader_idx}")
 
@@ -387,7 +393,9 @@ def on_predict_batch_start(
         if not self.has_dataloader_changed(dataloader_idx):
             return
 
-        self.predict_progress_bar.reset(convert_inf(self.total_predict_batches_current_dataloader))
+        total = convert_inf(self.total_
```

## Moved from `brief.md`

## Files That May Need Changes

- `src/lightning/pytorch/callbacks/progress/tqdm_progress.py`
