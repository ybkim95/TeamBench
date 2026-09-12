# Reference solution — GH1183_mlflow_21797

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1183_mlflow_21797`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1183_mlflow_21797/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `mlflow/server/jobs/utils.py` (modified, +5/-1)
- `tests/server/jobs/test_jobs.py` (modified, +30/-0)

## Diff Summary (What the Fix Changes)

### `mlflow/server/jobs/utils.py`
```diff
@@ -617,7 +617,11 @@ def _enqueue_unfinished_jobs(server_launching_timestamp: int) -> None:
 
                 params = json.loads(job.params)
                 timeout = job.timeout
-                job_workspace = job.workspace or workspace or DEFAULT_WORKSPACE_NAME
+                # Only propagate workspace to subprocess when workspaces are enabled
+                if MLFLOW_ENABLE_WORKSPACES.get():
+                    job_workspace = job.workspace or workspace or DEFAULT_WORKSPACE_NAME
+                else:
+                    job_workspace = None
                 # Look up exclusive flag from function metadata
                 fn_fullname = get_job_fn_fullname(job.job_name)
                 fn_metadata = _load_function(fn_fullname)._job_fn_metadata
```

## Moved from `brief.md`

## Files That May Need Changes

- `mlflow/server/jobs/utils.py`
