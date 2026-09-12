# Reference solution — GH1123_airflow_63848

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1123_airflow_63848`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1123_airflow_63848/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `airflow-core/src/airflow/assets/manager.py` (modified, +1/-1)
- `airflow-core/tests/unit/assets/test_manager.py` (modified, +23/-0)

## Diff Summary (What the Fix Changes)

### `airflow-core/src/airflow/assets/manager.py`
```diff
@@ -357,7 +357,7 @@ def _queue_dagruns(
         )
 
         non_partitioned_dags = dags_to_queue.difference(partition_dags)  # don't double process
-        if not non_partitioned_dags:
+        if not non_partitioned_dags or partition_key is not None:
             return None
 
         # Possible race condition: if multiple dags or multiple (usually
```

## Moved from `brief.md`

## Files That May Need Changes

- `airflow-core/src/airflow/assets/manager.py`
