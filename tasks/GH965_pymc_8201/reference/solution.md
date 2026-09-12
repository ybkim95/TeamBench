# Reference solution — GH965_pymc_8201

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH965_pymc_8201`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH965_pymc_8201/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `pymc/progress_bar/marimo_progress.py` (modified, +1/-6)
- `pymc/progress_bar/progress.py` (modified, +4/-2)
- `pymc/progress_bar/rich_progress.py` (modified, +14/-14)
- `pymc/smc/parallel.py` (modified, +3/-1)
- `pymc/smc/sampling.py` (modified, +3/-1)
- `tests/progress_bar/test_manager.py` (modified, +133/-77)
- `tests/progress_bar/test_marimo.py` (modified, +32/-0)

## Diff Summary (What the Fix Changes)

### `pymc/progress_bar/marimo_progress.py`
```diff
@@ -183,12 +183,7 @@ def update(
         self._task_state[task_id]["stats"] = stats
 
         if is_last:
-            # Ensure bar is fully filled on completion
-            total = self._task_state[task_id]["total"]
-            completed = self._task_state[task_id]["completed"]
-            remaining = total - completed
-            if remaining > 0:
-                self._task_state[task_id]["completed"] = total
+            self._task_state[task_id]["completed"] = self._task_state[task_id]["total"]
 
         self._render()
 
```

### `pymc/progress_bar/progress.py`
```diff
@@ -310,13 +310,15 @@ def update(self, chain_idx: int, is_last: bool, draw: int, tuning: bool, stats)
         if not self._show_progress:
             return
 
-        self.completed_draws += 1
+        if not is_last:
+            self.completed_draws += 1
+
         if self.combined_progress:
             draw = self.completed_draws
             chain_idx = 0
 
         failing, all_step_stats = self._extract_stats(stats)
-        all_step_stats["draws"] = draw
+        all_step_stats["draws"] = draw + 1 if not self.combined_progress else draw
 
         self._backend.update(
             task_id=chain_idx,
```

### `pymc/progress_bar/rich_progress.py`
```diff
@@ -231,7 +231,7 @@ def _initialize_tasks(self) -> None:
                 self._progress.add_task(
                     "Sampling",
                     completed=0,
-                    total=self.total * self.n_bars - 1,
+                    total=self.total * self.n_bars,
                     task_idx=0,
                     sampling_speed=0,
                     speed_unit="draws/s",
@@ -244,7 +244,7 @@ def _initialize_tasks(self) -> None:
                 self._progress.add_task(
                     "Sampling",
                     completed=0,
-                    total=self.total - 1,
+                    total=self.total,
                     task_idx=task_idx,
                     sampling_speed=0,
                     speed_unit="draws/s",
@@ -281,6 +281,18 @@ def update(
         if rich_task_id is None:
             return
 
+        if is_last:
+            self._progress.update(
+                rich_task_id,
+                completed=self.total if not self.combined else self.total * self.n_bars,
+                sampling_speed=0,
+                speed_unit="",
+                failing=failing,
+                refresh=True,
+                **stats,
+            )
+            return
+
         self._progress.advance(rich_task_id, advance=advance)
 
         task = self._progress.tasks[task_id]
@@ -303,18 +315,6 @@ def update(
             **stats,
         )
 
-        if is_last:
-            # Ensure bar is fully filled on completion
-            remaining = task.total - task.completed if task.total else 0
-            if remaining > 0:
-                self._progress.advance(rich_task_id, advance=remaining)
-            self._progress.update(
-                rich_task_id,
-                failing=failing,
-                **stats,
-                refresh=True,
-            )
-
 
 def RichSimpleProgress(theme: Theme | None):
     return CustomProgress(
```

### `pymc/smc/parallel.py`
```diff
@@ -402,7 +402,9 @@ def __iter__(self):
                         sample_settings,
                     ) = result[2:]
 
-                    progress_manager.update(proc.chain, stage, beta, is_last=True)
+                    old_beta = chain_betas[proc.chain]
+                    chain_betas[proc.chain] = beta
+                    progress_manager.update(proc.chain, stage, beta, old_beta, is_last=True)
 
                     proc.join()
                     self._active.remove(proc)
```

### `pymc/smc/sampling.py`
```diff
@@ -482,7 +482,9 @@ def _sample_smc_sequentially(
 
                 stage += 1
 
-            progress_manager.update(chain_idx=i, stage=stage, beta=kernel.beta, is_last=True)
+            progress_manager.update(
+                chain_idx=i, stage=stage, beta=kernel.beta, old_beta=kernel.beta, is_last=True
+            )
 
             trace = _build_trace_from_kernel_state(
                 tempered_posterior=kernel.tempered_posterior,
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `pymc/progress_bar/marimo_progress.py`
- `pymc/progress_bar/progress.py`
- `pymc/progress_bar/rich_progress.py`
- `pymc/smc/parallel.py`
- `pymc/smc/sampling.py`
