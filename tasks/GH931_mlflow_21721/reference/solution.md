# Reference solution — GH931_mlflow_21721

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH931_mlflow_21721`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH931_mlflow_21721/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/docs/genai/tracing/prod-tracing.mdx` (modified, +7/-6)
- `mlflow/environment_variables.py` (modified, +15/-0)
- `mlflow/server/__init__.py` (modified, +6/-0)
- `mlflow/tracing/export/mlflow_v3.py` (modified, +56/-10)
- `tests/gateway/test_tracing_utils.py` (modified, +48/-0)
- `tests/server/test_init.py` (modified, +5/-1)
- `tests/tracing/export/test_mlflow_v3_attachments.py` (modified, +2/-0)
- `tests/tracing/export/test_mlflow_v3_exporter.py` (modified, +157/-0)

## Diff Summary (What the Fix Changes)

### `mlflow/environment_variables.py`
```diff
@@ -1130,6 +1130,21 @@ def get(self):
 #: (default: ``None``)
 MLFLOW_TRACING_SQL_WAREHOUSE_ID = _EnvironmentVariable("MLFLOW_TRACING_SQL_WAREHOUSE_ID", str, None)
 
+#: Specifies whether to export spans incrementally as they complete, in addition to
+#: exporting the full trace. When enabled, spans are written to the tracking store
+#: individually via ``log_spans`` as each span finishes. This provides real-time span
+#: visibility for long-running traces but adds extra DB round-trips that may increase
+#: latency under high concurrency. When disabled, spans are batch-written to the database
+#: at trace completion instead of individually during the request. This removes real-time
+#: visibility for in-progress traces but reduces DB contention. Remote/distributed trace
+#: spans (from ``traceparent`` headers) are still exported incrementally when the backend
+#: supports ``log_spans``, as they cannot be persisted through the full trace export path.
+#: The MLflow tracking server disables this by default to reduce DB contention.
+#: (default: ``True``)
+MLFLOW_ENABLE_INCREMENTAL_SPAN_EXPORT = _BooleanEnvironmentVariable(
+    "MLFLOW_ENABLE_INCREMENTAL_SPAN_EXPORT", True
+)
+
 
 #: Specifies the location to send traces to. This can be either an MLflow experiment ID or a
 #: Databricks Unity Catalog (UC) schema (format: `<catalog_name>.<schema_name>`).
```

### `mlflow/server/__init__.py`
```diff
@@ -20,6 +20,7 @@
 from mlflow.environment_variables import (
     _MLFLOW_INTERNAL_GATEWAY_AUTH_TOKEN,
     _MLFLOW_SGI_NAME,
+    MLFLOW_ENABLE_INCREMENTAL_SPAN_EXPORT,
     MLFLOW_FLASK_SERVER_SECRET_KEY,
     MLFLOW_SERVER_ENABLE_JOB_EXECUTION,
 )
@@ -382,6 +383,11 @@ def _run_server(
     if secret_key := MLFLOW_FLASK_SERVER_SECRET_KEY.get():
         env_map[MLFLOW_FLASK_SERVER_SECRET_KEY.name] = secret_key
 
+    # Disable incremental span export by default to reduce DB contention from
+    # concurrent gateway requests. Users can override by setting the env var explicitly.
+    if not MLFLOW_ENABLE_INCREMENTAL_SPAN_EXPORT.is_set():
+        env_map[MLFLOW_ENABLE_INCREMENTAL_SPAN_EXPORT.name] = "false"
+
     # Determine which server we're using (only one should be true)
     using_gunicorn = gunicorn_opts is not None
     using_waitress = waitress_opts is not None
```

### `mlflow/tracing/export/mlflow_v3.py`
```diff
@@ -9,7 +9,10 @@
 from mlflow.entities.span import Span
 from mlflow.entities.trace import Trace
 from mlflow.entities.trace_info import TraceInfo
-from mlflow.environment_variables import MLFLOW_ENABLE_ASYNC_TRACE_LOGGING
+from mlflow.environment_variables import (
+    MLFLOW_ENABLE_ASYNC_TRACE_LOGGING,
+    MLFLOW_ENABLE_INCREMENTAL_SPAN_EXPORT,
+)
 from mlflow.exceptions import RestException
 from mlflow.tracing.client import TracingClient
 from mlflow.tracing.constant import SpansLocation, TraceTagKey
@@ -45,10 +48,14 @@ def __init__(self, tracking_uri: str | None = None) -> None:
         # Display handler is no-op when running outside of notebooks.
         self._display_handler = get_display_handler()
 
-        # A flag to cache the failure of exporting spans so that the client will not try to export
-        # spans again and trigger excessive server side errors. Default to True (optimistically
-        # assume the store supports span-level logging).
-        self._should_export_spans_incrementally = True
+        # Controls whether spans are exported incrementally via log_spans().
+        self._should_export_spans_incrementally = MLFLOW_ENABLE_INCREMENTAL_SPAN_EXPORT.get()
+
+        # Tracks whether the store supports span-level logging. Set to False at runtime
+        # if log_spans() raises NotImplementedError or returns a 501. This is separate from
+        # _should_export_spans_incrementally so that disabling incremental export (e.g. for
+        # the gateway) doesn't prevent remote/distributed traces from being exported.
+        self._store_supports_log_spans = True
 
     def export(self, spans: Sequence[ReadableSpan]) -> None:
         """
@@ -59,11 +66,29 @@ def export(self, spans: Sequence[ReadableSpan]) -> None:
                 a span processor. All spans (root and non-root) are exported.
         """
 
-        if self._should_export_spans_incrementally:
+        if self._should_export_spans_incrementally and self._store_supports_log_sp
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `mlflow/environment_variables.py`
- `mlflow/server/__init__.py`
- `mlflow/tracing/export/mlflow_v3.py`
