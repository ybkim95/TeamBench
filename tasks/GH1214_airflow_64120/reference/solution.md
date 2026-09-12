# Reference solution — GH1214_airflow_64120

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1214_airflow_64120`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1214_airflow_64120/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `task-sdk/src/airflow/sdk/definitions/connection.py` (modified, +1/-1)
- `task-sdk/tests/task_sdk/definitions/test_connection.py` (modified, +9/-0)

## Diff Summary (What the Fix Changes)

### `task-sdk/src/airflow/sdk/definitions/connection.py`
```diff
@@ -151,7 +151,7 @@ def __init__(self, *, conn_id: str, uri: str | None = None, **kwargs) -> None:
         if uri is None:
             self.__attrs_init__(conn_id=conn_id, **kwargs)  # type: ignore[attr-defined]
         else:
-            self.__dict__.update(self.from_uri(uri, conn_id=conn_id).to_dict(validate=False))
+            self.__dict__.update(attrs.asdict(self.from_uri(uri, conn_id=conn_id), recurse=False))
 
     def get_uri(self) -> str:
         """Generate and return connection in URI format."""
```

## Moved from `brief.md`

## Files That May Need Changes

- `task-sdk/src/airflow/sdk/definitions/connection.py`
