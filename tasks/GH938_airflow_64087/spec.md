# GH938_airflow_64087: Fix DagRun._emit_dagrun_span crash on None/empty context_carrier — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/apache/airflow

## PR Description

## Summary

  Fixes a crash in `DagRun._emit_dagrun_span()` when `context_carrier` is `None` or empty `{}`.

  - **Symptom**: `AttributeError: 'NoneType' object has no attribute 'get'` in `TraceContextTextMapPropagator().extract()`
  - **Cause**: DagRuns created before OTel tracing was enabled have `context_carrier = NULL` in the database. When these DagRuns complete, `_emit_dagrun_span()` passes `None` directly to `extract()`.
  - **Fix**: Early return when `context_carrier` is falsy, consistent with the existing guard in `task_runner.py:148`.

  ## Reproduction Path

  1. Have existing DagRuns in the database (created before OTel was enabled → `context_carrier = NULL`)
  2. Enable OTel tracing
  3. Those DagRuns complete → `update_state()` → `_emit_dagrun_span()` → crash

  **Note**: This supersedes #61655 which targeted `OtelTrace.extract()` — that class was since removed in #63452.

  ## Testing

  - Added parametrized unit test covering both `None` and `{}` carrier values
  - Verified no span is emitted when carrier is missing (graceful skip)

  ---
  **Was generative AI tooling used to co-author this PR?**
  - [X] Yes (please specify the tool below)
  Generated-by: Claude (Anthropic) following [the guidelines](https://github.com/apache/airflow/blob/main/contributing-docs/05_pull_requests.rst#gen-ai-assisted-contributions)

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
