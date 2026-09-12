# Reference solution — GH930_mlflow_1758

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH930_mlflow_1758`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH930_mlflow_1758/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `mlflow/store/sqlalchemy_store.py` (modified, +13/-5)
- `tests/store/test_sqlalchemy_store.py` (modified, +30/-0)

## Diff Summary (What the Fix Changes)

### `mlflow/store/sqlalchemy_store.py`
```diff
@@ -9,7 +9,7 @@
 
 from mlflow.entities.lifecycle_stage import LifecycleStage
 from mlflow.store import SEARCH_MAX_RESULTS_THRESHOLD
-from mlflow.store.dbmodels.db_types import MYSQL
+from mlflow.store.dbmodels.db_types import MYSQL, MSSQL
 from mlflow.store.dbmodels.models import Base, SqlExperiment, SqlRun, SqlMetric, SqlParam, SqlTag, \
     SqlExperimentTag
 from mlflow.entities import RunStatus, SourceType, Experiment
@@ -159,14 +159,22 @@ def make_managed_session():
 
         return make_managed_session
 
-    def _set_no_auto_for_zero_values(self, session):
+    def _set_zero_value_insertion_for_autoincrement_column(self, session):
         if self.db_type == MYSQL:
+            # config letting MySQL override default
+            # to allow 0 value for experiment ID (auto increment column)
             session.execute("SET @@SESSION.sql_mode='NO_AUTO_VALUE_ON_ZERO';")
+        if self.db_type == MSSQL:
+            # config letting MSSQL override default
+            # to allow any manual value inserted into IDENTITY column
+            session.execute("SET IDENTITY_INSERT experiments ON;")
 
     # DB helper methods to allow zero values for columns with auto increments
-    def _unset_no_auto_for_zero_values(self, session):
+    def _unset_zero_value_insertion_for_autoincrement_column(self, session):
         if self.db_type == MYSQL:
             session.execute("SET @@SESSION.sql_mode='';")
+        if self.db_type == MSSQL:
+            session.execute("SET IDENTITY_INSERT experiments OFF;")
 
     def _create_default_experiment(self, session):
         """
@@ -196,11 +204,11 @@ def decorate(s):
         values = ", ".join([decorate(default_experiment.get(c)) for c in columns])
 
         try:
-            self._set_no_auto_for_zero_values(session)
+            self._set_zero_value_insertion_for_autoincrement_column(session)
             session.execute("INSERT INTO {} ({}) VALUES ({});".format(
                 table, ", ".join(columns), values))
     
```

## Moved from `brief.md`

## Files That May Need Changes

- `mlflow/store/sqlalchemy_store.py`
