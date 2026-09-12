# Reference solution — GH1102_darts_2895

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1102_darts_2895`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1102_darts_2895/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CHANGELOG.md` (modified, +2/-0)
- `darts/models/forecasting/torch_forecasting_model.py` (modified, +2/-0)
- `darts/tests/models/forecasting/test_global_forecasting_models.py` (modified, +20/-5)

## Diff Summary (What the Fix Changes)

### `darts/models/forecasting/torch_forecasting_model.py`
```diff
@@ -1320,6 +1320,8 @@ def _train(
                 val_dataloaders=val_loader,
                 ckpt_path=ckpt_path,
             )
+        else:
+            trainer.strategy.connect(model)
         self.model = model
         self.trainer = trainer
 
```

## Moved from `brief.md`

## Files That May Need Changes

- `darts/models/forecasting/torch_forecasting_model.py`
