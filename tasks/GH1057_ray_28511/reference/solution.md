# Reference solution — GH1057_ray_28511

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1057_ray_28511`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1057_ray_28511/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `python/ray/tune/execution/ray_trial_executor.py` (modified, +26/-6)
- `python/ray/tune/execution/trial_runner.py` (modified, +17/-5)
- `python/ray/tune/schedulers/pbt.py` (modified, +8/-10)
- `python/ray/tune/tests/test_trial_scheduler.py` (modified, +9/-8)
- `python/ray/tune/tests/test_trial_scheduler_pbt.py` (modified, +99/-0)

## Diff Summary (What the Fix Changes)

### `python/ray/tune/execution/ray_trial_executor.py`
```diff
@@ -498,7 +498,6 @@ def _stop_trial(
         Args:
             error: Whether to mark this trial as terminated in error.
             exc: Optional exception.
-
         """
         self.set_status(trial, Trial.ERROR if error or exc else Trial.TERMINATED)
         self._trial_just_finished = True
@@ -602,27 +601,48 @@ def stop_trial(
         error: bool = False,
         exc: Optional[Union[TuneError, RayTaskError]] = None,
     ) -> None:
+        """Stops the trial, releasing held resources and removing futures related to
+        this trial from the execution queue.
+
+        Args:
+            trial: Trial to stop.
+            error: Whether to mark this trial as terminated in error. The trial status
+                will be set to either `Trial.ERROR` or `Trial.TERMINATED` based on this.
+                Defaults to False.
+            exc: Optional exception to log (as a reason for stopping). Defaults to None.
+        """
         prior_status = trial.status
         if prior_status == Trial.RUNNING:
             logger.debug("Trial %s: Returning resources.", trial)
             out = self._find_future(trial)
             for result_id in out:
                 self._futures.pop(result_id)
+        trial.saving_to = None
         self._stop_trial(trial, error=error or exc, exc=exc)
 
     def continue_training(self, trial: Trial) -> None:
         """Continues the training of this trial."""
         self._train(trial)
 
-    def pause_trial(self, trial: Trial) -> None:
-        """Pauses the trial.
+    def pause_trial(self, trial: Trial, should_checkpoint: bool = True) -> None:
+        """Pauses the trial, releasing resources (specifically GPUs)
+
+        We do this by:
+        1. Checkpoint the trial (if `should_checkpoint`) in memory to allow us to resume
+        from this state in the future. We may not always  want to checkpoint, if we
+        know that the checkpoint will not be used.
+        2. Stop the trial and release resources, see `RayT
```

### `python/ray/tune/execution/trial_runner.py`
```diff
@@ -977,10 +977,9 @@ def _on_training_result(self, trial, result):
     def _post_process_on_training_saving_result(self, trial):
         # `self._queued_trial_decisions` now contains a final decision
         # based on all results
-        if trial not in self._cached_trial_decisions:
-            final_decision = self._queued_trial_decisions.pop(trial.trial_id, None)
-            if final_decision:
-                self._execute_action(trial, final_decision)
+        final_decision = self._queued_trial_decisions.pop(trial.trial_id, None)
+        if final_decision:
+            self._execute_action(trial, final_decision)
 
     def _on_executor_error(self, trial, e: Union[RayTaskError, TuneError]):
         error_msg = f"Trial {trial}: Error processing event."
@@ -1295,7 +1294,7 @@ def _execute_action(self, trial: Trial, decision: str):
         if decision == TrialScheduler.CONTINUE:
             self.trial_executor.continue_training(trial)
         elif decision == TrialScheduler.PAUSE:
-            self.trial_executor.pause_trial(trial)
+            self.pause_trial(trial)
         elif decision == TrialScheduler.STOP:
             self.stop_trial(trial)
         elif decision == TrialScheduler.NOOP:
@@ -1427,6 +1426,19 @@ def _process_stop_requests(self):
             t = self._stop_queue.pop()
             self.stop_trial(t)
 
+    def pause_trial(self, trial: Trial, should_checkpoint: bool = True):
+        """Pause a trial and reset the necessary state variables for resuming later.
+
+        Args:
+            trial: Trial to pause.
+            should_checkpoint: Whether or not an in-memory checkpoint should be created
+                for this paused trial. Defaults to True.
+        """
+        # NOTE: The cached trial decision is not needed since we will overrule this
+        # decision with PAUSE.
+        self._cached_trial_decisions.pop(trial.trial_id, None)
+        self.trial_executor.pause_trial(trial, should_checkpoint=should_checkpoint)
+
 
```

### `python/ray/tune/schedulers/pbt.py`
```diff
@@ -449,7 +449,7 @@ def on_trial_result(
                     decision = TrialScheduler.PAUSE
                     break
             self._checkpoint_or_exploit(
-                trial, trial_runner.trial_executor, upper_quantile, lower_quantile
+                trial, trial_runner, upper_quantile, lower_quantile
             )
             return TrialScheduler.NOOP if trial.status == Trial.PAUSED else decision
         else:
@@ -476,7 +476,7 @@ def on_trial_result(
                     logger.debug("Perturbing Trial {}".format(t))
                     self._trial_state[t].last_perturbation_time = time
                     self._checkpoint_or_exploit(
-                        t, trial_runner.trial_executor, upper_quantile, lower_quantile
+                        t, trial_runner, upper_quantile, lower_quantile
                     )
 
                 all_train_times = [
@@ -522,11 +522,12 @@ def _save_trial_state(
     def _checkpoint_or_exploit(
         self,
         trial: Trial,
-        trial_executor: "trial_runner.RayTrialExecutor",
+        trial_runner: "trial_runner.TrialRunner",
         upper_quantile: List[Trial],
         lower_quantile: List[Trial],
     ):
         """Checkpoint if in upper quantile, exploits if in lower."""
+        trial_executor = trial_runner.trial_executor
         state = self._trial_state[trial]
         if trial in upper_quantile:
             # The trial last result is only updated after the scheduler
@@ -554,7 +555,7 @@ def _checkpoint_or_exploit(
                     " Skip exploit for Trial {}".format(trial)
                 )
                 return
-            self._exploit(trial_executor, trial, trial_to_clone)
+            self._exploit(trial_runner, trial, trial_to_clone)
 
     def _log_config_on_step(
         self,
@@ -605,7 +606,7 @@ def _get_new_config(self, trial, trial_to_clone):
 
     def _exploit(
         self,
-        trial_executor: "trial_runner.RayTrialExecutor",
+        trial_runner: "trial_runn
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `python/ray/tune/execution/ray_trial_executor.py`
- `python/ray/tune/execution/trial_runner.py`
- `python/ray/tune/schedulers/pbt.py`
