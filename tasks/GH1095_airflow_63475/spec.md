# GH1095_airflow_63475: fix(providers/standard): add response_timeout to HITLOperator to prevent race with execution_timeout — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/apache/airflow/issues/55866
- Repo: https://github.com/apache/airflow

## Issue Description

### Apache Airflow version

main (development)

### If "Other Airflow 2 version" selected, which one?

_No response_

### What happened?

In Airflow 3.1.0b2’s [HITLOperator](https://github.com/apache/airflow/blob/922f344af63c2199ff72f6d8c7080475be9c7a2c/providers/standard/src/airflow/providers/standard/operators/hitl.py#L48), the constructor doesn’t special-case `execution_timeout`, so it is passed straight through to `BaseOperator` via `super().__init__(**kwargs)`. Later, in `execute()`, the operator also reads `self.execution_timeout` to compute a `timeout_datetime` for the `HITLTrigger`:

https://github.com/apache/airflow/blob/922f344af63c2199ff72f6d8c7080475be9c7a2c/providers/standard/src/airflow/providers/standard/operators/hitl.py#L145-L155

Because `execution_timeout` on `BaseOperator` starts counting from task start, the task can hit a `timeout` before it reaches `.defer()`. This is especially likely if `execution_timeout` is short or if notifiers (e.g., `SmtpNotifier`) take non-trivial time. In my run, with `execution_timeout=timedelta(seconds=1)` and a notifier that takes >1s, the task timed out during `notifier(context)` and never deferred, defeating the intended “wait for human input until timeout” behavior.

### What you think should happen instead?

`execution_timeout` should not be used for the HITL waiting window. The operator should:

* Introduce a separate parameter (e.g., `response_timeout` / `hitl_timeout`) that controls how long the `HITLTrigger` waits, independent of `BaseOperator.execution_timeout`.

* In `__init__`, compare `hitl_timeout` against `execution_timeout` to ensure consistency (i.e. `execution_timeout` should always be longer than `hitl_timeout`). If not, raise a clear validation error.

This way, notifiers and pre-defer work can run without racing the base operator timeout, and the HITL “response window” is enforced where intended—by the trigger.

### How to reproduce

Minimal DAG:

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.hitl import HITLOperator

def slow_notifier(context):
    import time
    time.sleep(2)  # emulate slow SMTP or webhook

with DAG(
    dag_id="hitl_timeout_repro",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
) as dag:
    HITLOperator(
        task_id="hitl_wait_for_user",
        subject="Please approve",
        body="Click approve/deny.",
        options=["approve", "deny"],
        defaults={"auto": "deny"},
        notifiers=[slow_notifier],
        # IMPORTANT: short execution timeout to trigger the bug
        execution_timeout=timedelta(seconds=1),
    )
```

### Operating System

LM 21.3 with docker python:3.12-slim-bookworm

### Versions of Apache Airflow Providers

_No response_

### Deployment

Docker-Compose

### Deployment details

_No response_

### Anything else?

_No response_

### Are you willing to submit PR?

- [x] Yes I am willing to submit a PR!

### Code of Conduct

- [x] I agree to follow this project's [Code of Conduct](https://github.com/apache/airflow/blob/main/CODE_OF_CONDUCT.md)

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I'd like to work on this. The fix would introduce a dedicated `response_timeout` parameter in HITLOperator to separate the human-response wait window from BaseOperator's `execution_timeout`, with backward-compatible deprecation for existing usage.

### Comment 2 ([user]):

A minimal fix path would be to stop overloading execution_timeout for two different semantics. I’d add a dedicated 
esponse_timeout: timedelta | None for the HITL wait window, compute the trigger deadline from that field only, and keep execution_timeout as the outer task guard. For compatibility, if 
esponse_timeout is None and execution_timeout is not None, you can temporarily map 
esponse_timeout = execution_timeout with a deprecation warning. It would also help to validate execution_timeout > notifier_budget + response_timeout when both are set, so slow notifiers do not consume the entire human-response window before defer() happens. A focused regression test is: use a notifier that sleeps ~2s, set execution_timeout=1s, 
esponse_timeout=10s, and assert the task still defers instead of timing out in the pre-defer path.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
