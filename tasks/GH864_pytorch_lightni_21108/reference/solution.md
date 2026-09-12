# Reference solution — GH864_pytorch_lightni_21108

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH864_pytorch_lightni_21108`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH864_pytorch_lightni_21108/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `src/lightning/pytorch/CHANGELOG.md` (modified, +3/-0)
- `src/lightning/pytorch/callbacks/progress/rich_progress.py` (modified, +1/-2)
- `tests/tests_pytorch/callbacks/progress/test_rich_progress_bar.py` (modified, +28/-0)

## Diff Summary (What the Fix Changes)

### `src/lightning/pytorch/callbacks/progress/rich_progress.py`
```diff
@@ -390,8 +390,7 @@ def on_sanity_check_start(self, trainer: "pl.Trainer", pl_module: "pl.LightningM
 
     @override
     def on_sanity_check_end(self, trainer: "pl.Trainer", pl_module: "pl.LightningModule") -> None:
-        if self.progress is not None:
-            assert self.val_sanity_progress_bar_id is not None
+        if self.progress is not None and self.val_sanity_progress_bar_id is not None:
             self.progress.update(self.val_sanity_progress_bar_id, advance=0, visible=False)
         self.refresh()
 
```

## Moved from `brief.md`

## Files That May Need Changes

- `src/lightning/pytorch/callbacks/progress/rich_progress.py`
