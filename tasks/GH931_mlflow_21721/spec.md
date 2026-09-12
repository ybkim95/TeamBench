# GH931_mlflow_21721: Fix trace export DB contention by disabling incremental span export for gateway — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/mlflow/mlflow

## PR Description

### Related Issues/PRs

Relates to ML-61935
Part of benchmark suite PR: #21561

### What changes are proposed in this pull request?

Fix `UniqueViolation` and `DeadlockDetected` errors in the gateway's async trace export path under concurrent load with PostgreSQL.

**Root cause**: `MlflowV3SpanExporter.export()` enqueued two independent async tasks per trace — `log_spans()` and `start_trace()` — that raced on the same DB rows (`trace_info`, `trace_request_metadata`, `trace_tag`). With 50 concurrent requests and 10 async worker threads, this caused:
- `UniqueViolation` on `trace_request_metadata_pk` from concurrent INSERTs
- `DeadlockDetected` from circular lock dependencies between the two tasks
- Expensive rollback-then-SELECT retry paths in `start_trace()` under contention

**Fix**: Introduce `MLFLOW_ENABLE_INCREMENTAL_SPAN_EXPORT` env var (default: `True`) that controls whether spans are exported incrementally via `log_spans()` as each span completes. The `mlflow server` command auto-disables this unless the user explicitly sets it.

**Net effect when incremental export is disabled (server default)**:
1. Spans are **not** written to DB individually as they complete (eliminates contention)
2. At trace completion, `_log_trace()` calls `start_trace()` then batch-writes **all spans** to DB in a single `log_spans()` call
3. Since `log_spans()` sets `SPANS_LOCATION=TRACKING_STORE`, artifact upload is skipped — spans live in the DB, not in artifacts
4. Remote/distributed trace spans (from `traceparent` headers) are still exported incrementally in `export()`, since they have no root span and `_export_traces()` skips them

For gateway traces (short-lived, 2 spans, ~50-100ms), incremental span export adds no value — the trace completes before the first `log_spans` task even runs. Disabling it and batch-writing at completion eliminates the DB contention entirely while still populating the spans table.

**Changes**:
- `mlflow/environment_variables.py` — New `MLFLOW_ENABLE_INCREMENTAL_SPAN_EXPORT` boolean env var
- `mlflow/server/__init__.py` — Auto-disable for `mlflow server` subprocess via `env_map` (unless user explicitly sets it)
- `mlflow/tracing/export/mlflow_v3.py` — Read env var in `__init__`, batch-write spans in `_log_trace()` when incremental is off, still export remote spans incrementally
- `docs/docs/genai/tracing/prod-tracing.mdx` — Document the new env var
- `tests/` — Tests for env var behavior, batch-write, remote trace export, server init

**Benchmark results** (4 workers, 50 concurrency, PostgreSQL, 3 runs × 2000 req):

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| P50 | 324 ms | 163 ms | 2.0x |
| P99 | 1,378 ms | 488 ms | 2.8x |
| RPS | 111 | 233 | 2.1x |
| Failures | UniqueViolation, DeadlockDetected | 0 | Eliminated |

### How is this PR tested?

- [x] Existing unit/integration tests
- [x] New unit/integration tests
- [x] Manual tests

New tests:
- `test_should_export_spans_incrementally_flag` — Parametrized test verifying env var controls `log_spans` calls
- `test_remote_trace_exported_when_incremental_export_disabled` — Verifies distributed mirror spans are still exported when incremental is off
- `test_maybe_traced_gateway_call_with_traceparent_incremental_export_disabled` — Gateway distributed tracing regression test
- `test_run_server_with_uvicorn` — Verifies `MLFLOW_ENABLE_INCREMENTAL_SPAN_EXPORT` is set in server subprocess env

Ran gateway benchmark against PostgreSQL. Verified zero DB errors and improved latency.

### Does this PR require documentation update?

- [x] Yes. I've updated:
  - [x] Instructions

Updated `docs/docs/genai/tracing/prod-tracing.mdx` with the new env var.

### Does this PR require updating the [MLflow Skills](https://github.com/mlflow/skills) repository?

- [x] No.

### Release Notes

#### Is this a user-facing change?

- [x] Yes. Fix database contention (`UniqueViolation`, `DeadlockDetected`) in the AI Gateway's trace export path under concurrent load with PostgreSQL, improving throughput by 2.1x and eliminating DB errors. Spans are now batch-written to the database at trace completion instead of incrementally, controlled by `MLFLOW_ENABLE_INCREMENTAL_SPAN_EXPORT` (auto-disabled by `mlflow server`).

#### What component(s), interfaces, languages, and integrations does this PR affect?

Components

- [x] `area/gateway`: MLflow AI Gateway client APIs, server, and third-party integrations
- [x] `area/tracing`: MLflow Tracing features, tracing APIs, and LLM tracing functionality
- [x] `area/tracking`: Tracking Service, tracking client APIs, autologging

<a name="release-note-category"></a>

#### How should the PR be classified in the release notes? Choose one:

- [x] `rn/bug-fix` - A user-facing bug fix worth mentioning in the release notes

#### Is this PR a critical bugfix or security fix that should go into the next patch release?

- [ ] This PR is critical and needs to be in the next patch release
- [x] This PR can wait for the next minor release

This pull request was AI-assisted by Isaac.

## PR Review Comments

**[user]** on `mlflow/tracing/provider.py`:

🔴 **CRITICAL:** `write_spans_with_trace` can become `True` for any non-Databricks tracking URI (including `http(s)://` REST tracking servers or local `file:` stores) when `MLFLOW_ENABLE_ASYNC_TRACE_LOGGING` is set. In that mode the exporter passes `spans` into `TracingClient.start_trace()`, which will call `store.start_trace(..., spans=...)` — but several store implementations (e.g. `RestStore`, `FileStore`, `DatabricksTracingRestStore`) don’t accept a `spans` kwarg and will raise `TypeError`. Tighten the gating here to only enable this for backends that implement the new signature (e.g. SQLAlchemy DB URIs / SqlAlchemyStore), or update all store `start_trace` implementations to accept (and safely ignore) `spans`.

**[user]** on `mlflow/tracing/client.py`:

🔴 **CRITICAL:** `TracingClient.start_trace()` conditionally calls `self.store.start_trace(..., spans=spans)` when `spans` is provided, but multiple concrete tracking stores in the repo still define `start_trace(self, trace_info)` without a `spans` parameter. This will raise `TypeError` at runtime when `spans` is passed (e.g. from the V3 exporter when `write_spans_with_trace` is enabled). Either make all store implementations accept `spans: list[Span] | None = None` (ignoring it when unsupported) or add a backward-compatible fallback here (e.g. catch `TypeError` and retry without `spans`).

**[user]** on `mlflow/tracing/provider.py`:

🟡 **MODERATE:** `write_spans_with_trace` is enabled for any non-Databricks tracking URI when async logging is explicitly enabled, including `http(s)` tracking URIs. For REST backends that support OTLP span ingestion, this will disable `log_spans` and (since `RestStore.start_trace()` ignores `spans`) spans will no longer be stored in the tracking store (they’ll fall back to artifact upload instead). If the intent is to consolidate *DB* writes for SQLAlchemy backends, consider additionally gating this flag to SQLAlchemy/database schemes (or checking the resolved store type) so REST-based deployments don’t change span storage behavior.

**[user]** on `mlflow/tracing/export/mlflow_v3.py`:

🔴 **CRITICAL:** When `write_spans_with_trace` is enabled, `export()` skips `_export_spans_incrementally()` for *all* spans. This breaks distributed tracing / remote-span scenarios where spans are non-root (so `_export_traces()` ignores them) and therefore never get persisted. Consider still running incremental span export for traces marked `is_remote_trace` in `InMemoryTraceManager` (or otherwise gating consolidated mode to non-remote traces) so non-root remote spans continue to be exported.

**[user]** on `mlflow/tracing/provider.py`:

Doesn't this cause an issue when the file store/rest store is used? It seems spans are passed to `start_trace`, but that's ignored in these stores, resulting in no spans.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
