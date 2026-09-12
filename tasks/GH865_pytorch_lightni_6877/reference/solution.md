# Reference solution — GH865_pytorch_lightni_6877

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH865_pytorch_lightni_6877`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH865_pytorch_lightni_6877/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `pytorch_lightning/core/hooks.py` (modified, +5/-5)
- `pytorch_lightning/trainer/predict_loop.py` (modified, +0/-1)
- `pytorch_lightning/trainer/trainer.py` (modified, +5/-4)
- `tests/trainer/test_trainer.py` (modified, +32/-0)

## Diff Summary (What the Fix Changes)

### `pytorch_lightning/core/hooks.py`
```diff
@@ -114,13 +114,13 @@ def on_validation_model_eval(self) -> None:
         """
         Sets the model to eval during the val loop
         """
-        self.eval()
+        self.trainer.model.eval()
 
     def on_validation_model_train(self) -> None:
         """
         Sets the model to train during the val loop
         """
-        self.train()
+        self.trainer.model.train()
 
     def on_validation_batch_start(self, batch: Any, batch_idx: int, dataloader_idx: int) -> None:
         """
@@ -172,19 +172,19 @@ def on_test_model_train(self) -> None:
         """
         Sets the model to train during the test loop
         """
-        self.train()
+        self.trainer.model.train()
 
     def on_test_model_eval(self) -> None:
         """
         Sets the model to eval during the test loop
         """
-        self.eval()
+        self.trainer.model.eval()
 
     def on_predict_model_eval(self) -> None:
         """
         Sets the model to eval during the predict loop
         """
-        self.eval()
+        self.trainer.model.eval()
 
     def on_epoch_start(self) -> None:
         """
```

### `pytorch_lightning/trainer/predict_loop.py`
```diff
@@ -44,7 +44,6 @@ def on_predict_model_eval(self, *_, **__):
         model_ref.on_predict_model_eval()
 
     def setup(self, model, max_batches, dataloaders):
-        self.trainer.call_hook("on_predict_start")
 
         # copy properties for forward overrides
         self.trainer.model_connector.copy_trainer_model_properties(model)
```

### `pytorch_lightning/trainer/trainer.py`
```diff
@@ -582,11 +582,11 @@ def run_train(self) -> None:
         self.checkpoint_connector.has_trained = False
 
         # enable train mode
-        model = self.lightning_module
-        model.train()
+        self.model.train()
         torch.set_grad_enabled(True)
 
         # reload data when needed
+        model = self.lightning_module
         self.train_loop.reset_train_val_dataloaders(model)
 
         # hook
@@ -772,8 +772,6 @@ def run_evaluate(self):
         return eval_loop_results
 
     def run_predict(self):
-        self.predict_loop.on_predict_start()
-
         # prepare dataloaders
         dataloaders, max_batches = self.predict_loop.get_predict_dataloaders()
 
@@ -789,6 +787,9 @@ def run_predict(self):
         model.zero_grad()
         torch.set_grad_enabled(False)
 
+        # call hook
+        self.predict_loop.on_predict_start()
+
         # set up the eval loop
         self.predict_loop.setup(model, max_batches, dataloaders)
 
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `pytorch_lightning/core/hooks.py`
- `pytorch_lightning/trainer/predict_loop.py`
- `pytorch_lightning/trainer/trainer.py`
