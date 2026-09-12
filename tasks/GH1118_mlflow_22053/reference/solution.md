# Reference solution — GH1118_mlflow_22053

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1118_mlflow_22053`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1118_mlflow_22053/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `mlflow/genai/evaluation/harness.py` (modified, +13/-4)
- `tests/genai/evaluate/test_evaluation.py` (modified, +92/-2)

## Diff Summary (What the Fix Changes)

### `mlflow/genai/evaluation/harness.py`
```diff
@@ -234,6 +234,7 @@ def __init__(
         max_rps_multiplier: float,
         pool_workers: int,
         score_workers: int,
+        experiment_id: str | None,
     ):
         """
         Args:
@@ -248,10 +249,12 @@ def __init__(
             pool_workers: Number of threads in the predict pool.
             score_workers: Number of score-pool threads, used to size the
                 backpressure buffer that bounds predicted-but-not-yet-scored items.
+            experiment_id: MLflow experiment ID for trace/assessment logging.
         """
         self._eval_items = eval_items
         self._predict_fn = predict_fn
         self._run_id = run_id
+        self._experiment_id = experiment_id
         self._max_retries = max_retries
 
         self._limiter = _make_rate_limiter(
@@ -314,6 +317,7 @@ def _submit_all(self) -> None:
                     self._run_id,
                     self._limiter,
                     self._max_retries,
+                    self._experiment_id,
                 )
                 self._queue.put((future, i))
         except Exception as e:
@@ -401,7 +405,6 @@ def __init__(
         self._session_groups = session_groups
         self._run_id = run_id
         self._max_retries = max_retries
-
         self._limiter = _make_rate_limiter(
             rps, adaptive=adaptive, max_rps_multiplier=max_rps_multiplier
         )
@@ -504,6 +507,7 @@ def _run_pipeline(
     run_id: str | None,
     progress_bar,
     multi_turn_assessments: dict[str, list[Feedback]],
+    experiment_id: str | None,
 ) -> tuple[list[float], list[float]]:
     """Run the predict→score pipeline and multi-turn scoring.
 
@@ -532,6 +536,7 @@ def _run_pipeline(
         max_rps_multiplier=_AIMD_UPPER_MULTIPLIER,
         pool_workers=predict_workers,
         score_workers=score_workers,
+        experiment_id=experiment_id,
     )
     scorer_submitter = _ScoreSubmitter(
         eval_items,
@@ -657,6 +662,7 @@ def run(
             run_id=run_id,
           
```

## Moved from `brief.md`

## Files That May Need Changes

- `mlflow/genai/evaluation/harness.py`
