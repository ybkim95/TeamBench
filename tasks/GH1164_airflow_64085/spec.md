# GH1164_airflow_64085: Fix AwsBaseWaiterTrigger losing error details on deferred task failure — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/apache/airflow

## PR Description

> **Note:** This PR is blocked until all underlying operators are updated to handle the new error trigger event. Otherwise, these operators will fail silently.

When a deferred AWS task hits a terminal failure state, `async_wait()` raises
`AirflowException` with the error details. But `AwsBaseWaiterTrigger.run()` did
not catch it — the exception propagated to the triggerer framework which replaced
it with a generic "Trigger failure" message. `execute_complete()` was never called,
so operators and `on_failure_callback` lost all error context.

**Fix:** Catch `AirflowException` in `run()` and yield
`TriggerEvent(status="error", message=str(e))`, routing failures through
`execute_complete()` where operators handle non-success events.

Also adds `"JobRun.ErrorMessage"` to `GlueJobCompleteTrigger.status_queries` so the
actual Glue error text is included alongside `JobRunState`.

related: https://github.com/apache/airflow/discussions/63706
Closes: https://github.com/apache/airflow/issues/64095

## Tested on EC2 with real Glue job

Ran a Glue job designed to fail with `GlueJobOperator(deferrable=True)`.

**Before (bug):** `on_failure_callback` receives `TaskDeferralError("Trigger failure")` — no details.

**After (fix):**
```
[2026-03-20 22:53:41] INFO - Status of AWS Glue job is: RUNNING
[2026-03-20 22:53:52] INFO - Status of AWS Glue job is: RUNNING
[2026-03-20 22:54:02] INFO - Status of AWS Glue job is: RUNNING
[2026-03-20 22:54:12] INFO - Status of AWS Glue job is: RUNNING
[2026-03-20 22:54:22] INFO - Trigger fired event result=TriggerEvent<{'status': 'error',
    'message': 'AWS Glue job failed.: FAILED - RuntimeError: GLUE_TEST: Intentional failure
    to test error propagation in deferrable mode\nWaiter job_complete failed: Waiter
    encountered a terminal failure state: For expression "JobRun.JobRunState" we matched
    expected path: "FAILED"',
    'run_id': 'jr_a485d84c34f952e1c8d9d3199455d2d6eda07529034ceb7e1b554514d367f417'}>
[2026-03-20 22:54:25] ERROR - Task failed with exception
AirflowException: Error in glue job: {'run_id': 'jr_a485d84c...', 'status': 'error',
    'message': 'AWS Glue job failed.: FAILED - RuntimeError: GLUE_TEST: Intentional failure
    to test error propagation in deferrable mode...'}
File ".../providers/amazon/src/airflow/providers/amazon/aws/operators/glue.py", line 345
    in execute_complete
```

- Trigger yields `TriggerEvent` with `status="error"` and full error message
- `execute_complete()` is called (stack trace shows `glue.py:345`) and raises with the details
- `on_failure_callback` receives the same `AirflowException` with actual Glue error

## Changes in this PR

### Core fix: `AwsBaseWaiterTrigger.run()` error handling
- `triggers/base.py` — Catch `AirflowException` from `async_wait()` and yield `TriggerEvent(status="error", message=str(e))` instead of letting it propagate
- `triggers/glue.py` — Add `"JobRun.ErrorMessage"` to `GlueJobCompleteTrigger.status_queries`
- `test_base.py`, `test_glue.py` — Tests for both changes

### Neptune operator fix (pre-existing bugs found during audit)
- `operators/neptune.py` — Both `NeptuneStartDbClusterOperator` and `NeptuneStopDbClusterOperator` had:
  - No error status validation — silently succeeded on failure
  - Wrong XCom key (`cluster_id` → should be `db_cluster_id`) — downstream tasks got empty string
  - Debug `self.log.info(event)` left in production code
  - Now uses `validate_execute_complete_event()` consistent with all other operators
- `test_neptune.py` — Updated trigger test to expect `TriggerEvent` instead of raised exception

## Operator compatibility audit — feedback requested

This change means `execute_complete()` will now be called with `status="error"` events
where previously it was never called on failure. I audited all 59 `execute_complete`
methods across AWS operators and sensors:

- **47 are safe** — use `validated_event["status"] != "success"` with raise
- **4 not affected** — their triggers override `run()` with own error handling
- **1 fixed in this PR** — Neptune (see above)
- **7 remaining** — would silently succeed on error events:

| Operator | Issue |
|----------|-------|
| [DmsDeleteReplicationConfigOperator](https://github.com/apache/airflow/blob/main/providers/amazon/src/airflow/providers/amazon/aws/operators/dms.py#L512) | No status check |
| [DmsStartReplicationOperator](https://github.com/apache/airflow/blob/main/providers/amazon/src/airflow/providers/amazon/aws/operators/dms.py#L707) | No status check |
| [DmsStopReplicationOperator](https://github.com/apache/airflow/blob/main/providers/amazon/src/airflow/providers/amazon/aws/operators/dms.py#L800) | No status check |
| [EmrServerlessStopApplicationOperator](https://github.com/apache/airflow/blob/main/providers/amazon/src/airflow/providers/amazon/aws/operators/emr.py#L1636) | `== "success"` with no else/raise |
| [EmrServerlessDeleteApplicationOperator](https://github.com/apache/airflow/blob/main/providers/amazon/src/airflow/providers/amazon/aws/operators/emr.py#L1743) | `== "success"` with no else/raise |
| [EmrServerlessStopApplicationOperator.stop_application](https://github.com/apache/airflow/blob/main/providers/amazon/src/airflow/providers/amazon/aws/operators/emr.py#L1619) | Deferred callback with same issue |
| [MwaaTaskSensor](https://github.com/apache/airflow/blob/main/providers/amazon/src/airflow/providers/amazon/aws/sensors/mwaa.py#L283) | `return None` unconditionally |

Merging the base trigger fix without addressing them would change their failure mode from "Trigger
failure" crash to silent success — which is worse.

**Reviewers:** Does the `TriggerEvent(status="error")` approach look right? If so, I'll
add commits to fix all 7 remaining operators in this PR before merge.

---

##### Was generative AI tooling used to co-author this PR?

- [X] Yes — Claude Code (Claude Opus 4.6)

Generated-by: Claude Code (Claude Opus 4.6) following [the guidelines](https://github.com/apache/airflow/blob/main/contributing-docs/05_pull_requests.rst#gen-ai-assisted-contributions)

## PR Review Comments

**[user]** on `providers/amazon/src/airflow/providers/amazon/aws/triggers/base.py`:

[user] 
Does the TriggerEvent(status="error") approach look right? If so, I'll
add commits to fix all 8 operators in this PR before we can merge.

**[user]** on `providers/amazon/src/airflow/providers/amazon/aws/operators/neptune.py`:

Is there a reason to drop `status` from the log here (and int he similar logs below)?

**[user]** on `providers/amazon/src/airflow/providers/amazon/aws/triggers/base.py`:

You don't see many try/except/else blocks.  I like it.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
