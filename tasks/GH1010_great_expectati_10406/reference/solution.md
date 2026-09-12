# Reference solution — GH1010_great_expectati_10406

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1010_great_expectati_10406`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1010_great_expectati_10406/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `great_expectations/compatibility/databricks.py` (modified, +1/-1)
- `great_expectations/execution_engine/sqlalchemy_execution_engine.py` (modified, +2/-0)
- `great_expectations/expectations/metrics/util.py` (modified, +56/-15)
- `great_expectations/expectations/regex_based_column_map_expectation.py` (modified, +3/-2)
- `pyproject.toml` (modified, +1/-0)
- `tests/datasource/fluent/integration/test_sql_datasources.py` (modified, +21/-7)

## Diff Summary (What the Fix Changes)

### `great_expectations/compatibility/databricks.py`
```diff
@@ -5,6 +5,6 @@
 )
 
 try:
-    from databricks import connect  # type: ignore[import-untyped]
+    from databricks import connect
 except ImportError:
     connect = DATABRICKS_CONNECT_NOT_IMPORTED
```

### `great_expectations/execution_engine/sqlalchemy_execution_engine.py`
```diff
@@ -378,6 +378,8 @@ def __init__(  # noqa: C901, PLR0912, PLR0913, PLR0915
             self.dialect_module = import_library_module(
                 module_name="clickhouse_sqlalchemy.drivers.base"
             )
+        elif self.dialect_name == GXSqlDialect.DATABRICKS:
+            self.dialect_module = import_library_module("databricks.sqlalchemy")
         else:
             self.dialect_module = None
 
```

### `great_expectations/expectations/metrics/util.py`
```diff
@@ -3,15 +3,18 @@
 import logging
 import re
 from collections import UserDict
+from types import ModuleType
 from typing import (
     TYPE_CHECKING,
     Any,
     Dict,
+    Iterable,
     List,
     Mapping,
     Optional,
     Sequence,
     Tuple,
+    Type,
     overload,
 )
 
@@ -63,6 +66,11 @@
 except ImportError:
     clickhouse_sqlalchemy = None
 
+try:
+    import databricks.sqlalchemy as sqla_databricks
+except ImportError:
+    sqla_databricks = None  # type: ignore[assignment]
+
 _BIGQUERY_MODULE_NAME = "sqlalchemy_bigquery"
 
 from great_expectations.compatibility import bigquery as sqla_bigquery
@@ -79,12 +87,33 @@
     teradatatypes = None
 
 
+def _is_databricks_dialect(dialect: ModuleType | sa.Dialect | Type[sa.Dialect]) -> bool:
+    """
+    Check if the Databricks dialect is being provided.
+    """
+    if not sqla_databricks:
+        return False
+    try:
+        if isinstance(dialect, sqla_databricks.DatabricksDialect):
+            return True
+        if hasattr(dialect, "DatabricksDialect"):
+            return True
+        if issubclass(dialect, sqla_databricks.DatabricksDialect):  # type: ignore[arg-type]
+            return True
+    except Exception:
+        pass
+    return False
+
+
 def get_dialect_regex_expression(  # noqa: C901, PLR0911, PLR0912, PLR0915
-    column, regex, dialect, positive=True
-):
+    column: sa.Column,
+    regex: str,
+    dialect: ModuleType | Type[sa.Dialect] | sa.Dialect,
+    positive: bool = True,
+) -> sa.SQLColumnExpression | None:
     try:
         # postgres
-        if issubclass(dialect.dialect, sa.dialects.postgresql.dialect):
+        if issubclass(dialect.dialect, sa.dialects.postgresql.dialect):  # type: ignore[union-attr]
             if positive:
                 return sqlalchemy.BinaryExpression(
                     column, sqlalchemy.literal(regex), sqlalchemy.custom_op("~")
@@ -96,11 +125,18 @@ def get_dialect_regex_expression(  # noqa: C901, PLR0911, PLR0912, PLR0915
     excep
```

### `great_expectations/expectations/regex_based_column_map_expectation.py`
```diff
@@ -87,8 +87,9 @@ def _sqlalchemy(cls, column, _dialect, **kwargs):
         regex_expression = get_dialect_regex_expression(column, cls.regex, _dialect)
 
         if regex_expression is None:
-            logger.warning(f"Regex is not supported for dialect {_dialect.dialect.name!s}")
-            raise NotImplementedError
+            msg = f"Regex is not supported for dialect {_dialect.dialect.name!s}"
+            logger.warning(msg)
+            raise NotImplementedError(msg)
 
         return regex_expression
 
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `great_expectations/compatibility/databricks.py`
- `great_expectations/execution_engine/sqlalchemy_execution_engine.py`
- `great_expectations/expectations/metrics/util.py`
- `great_expectations/expectations/regex_based_column_map_expectation.py`
