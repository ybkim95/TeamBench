# Reference solution — GH1034_airflow_64145

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1034_airflow_64145`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1034_airflow_64145/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `airflow-core/src/airflow/utils/db_manager.py` (modified, +26/-7)
- `airflow-core/tests/unit/utils/test_db_manager.py` (modified, +67/-1)

## Diff Summary (What the Fix Changes)

### `airflow-core/src/airflow/utils/db_manager.py`
```diff
@@ -196,27 +196,46 @@ class RunDBManager(LoggingMixin):
     """
 
     def __init__(self):
-        from airflow.api_fastapi.app import create_auth_manager
         from airflow.providers_manager import ProvidersManager
 
         super().__init__()
         self._managers: list[BaseDBManager] = []
 
-        # Start with auto-discovered DB managers from installed providers
+        # Start with auto-discovered DB managers from installed providers.
+        # ProvidersManager reads the ``db-managers`` key from each provider's
+        # get_provider_info() and is the primary source of truth.
         managers: list[str] = list(ProvidersManager().db_managers)
 
-        # Add any explicitly configured managers not already discovered
+        # Add any explicitly configured managers not already discovered.
         managers_config = conf.get("database", "external_db_managers", fallback=None)
         if managers_config:
             for m in managers_config.split(","):
                 if stripped := m.strip():
                     if stripped not in managers:
                         managers.append(stripped)
 
-        # Add DB manager declared by the configured auth manager (existing behavior, deduplicated)
-        auth_manager_db_manager = create_auth_manager().get_db_manager()
-        if auth_manager_db_manager and auth_manager_db_manager not in managers:
-            managers.append(auth_manager_db_manager)
+        # Add the DB manager declared by the configured auth manager as a
+        # final fallback for backward compatibility.
+        # This is wrapped in a try/except because in migration-only contexts
+        # (e.g. the Helm migrateDatabaseJob) the auth manager may not be fully
+        # initializable — a Flask app context or other runtime state may be
+        # absent.  A failure here must not silently drop the auth manager's DB
+        # manager from the migration list; ProvidersManager discovery above is
+        # the reliable path in those 
```

## Moved from `brief.md`

## Files That May Need Changes

- `airflow-core/src/airflow/utils/db_manager.py`
