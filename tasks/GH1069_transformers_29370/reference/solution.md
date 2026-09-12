# Reference solution — GH1069_transformers_29370

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1069_transformers_29370`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1069_transformers_29370/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `src/transformers/trainer.py` (modified, +11/-42)
- `tests/trainer/test_trainer.py` (modified, +1/-15)
- `tests/trainer/test_trainer_distributed.py` (modified, +0/-15)

## Diff Summary (What the Fix Changes)

### `src/transformers/trainer.py`
```diff
@@ -2491,21 +2491,13 @@ def _save_checkpoint(self, model, trial, metrics=None):
 
         run_dir = self._get_output_dir(trial=trial)
         output_dir = os.path.join(run_dir, checkpoint_folder)
-        if os.path.exists(output_dir) and len(os.listdir(output_dir)) > 0:
-            logger.warning(
-                f"Checkpoint destination directory {output_dir} already exists and is non-empty. "
-                "Saving will proceed but saved results may be invalid."
-            )
-            staging_output_dir = output_dir
-        else:
-            staging_output_dir = os.path.join(run_dir, f"tmp-{checkpoint_folder}")
-        self.save_model(staging_output_dir, _internal_call=True)
+        self.save_model(output_dir, _internal_call=True)
 
         if not self.args.save_only_model:
             # Save optimizer and scheduler
-            self._save_optimizer_and_scheduler(staging_output_dir)
+            self._save_optimizer_and_scheduler(output_dir)
             # Save RNG state
-            self._save_rng_state(staging_output_dir)
+            self._save_rng_state(output_dir)
 
         # Determine the new best metric / best model checkpoint
         if metrics is not None and self.args.metric_for_best_model is not None:
@@ -2525,39 +2517,16 @@ def _save_checkpoint(self, model, trial, metrics=None):
 
         # Save the Trainer state
         if self.args.should_save:
-            self.state.save_to_json(os.path.join(staging_output_dir, TRAINER_STATE_NAME))
+            self.state.save_to_json(os.path.join(output_dir, TRAINER_STATE_NAME))
 
         if self.args.push_to_hub:
-            self._push_from_checkpoint(staging_output_dir)
-
-        # Place checkpoint in final location after all saving is finished.
-        # First wait for everyone to finish writing
-        self.args.distributed_state.wait_for_everyone()
-
-        # Then go through the rewriting process, only renaming and rotating from main process(es)
-        if self.is_local_process_z
```

## Moved from `brief.md`

## Files That May Need Changes

- `src/transformers/trainer.py`
