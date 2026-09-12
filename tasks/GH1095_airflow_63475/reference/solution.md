# Reference solution — GH1095_airflow_63475

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1095_airflow_63475`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1095_airflow_63475/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `providers/standard/src/airflow/providers/standard/example_dags/example_hitl_operator.py` (modified, +2/-2)
- `providers/standard/src/airflow/providers/standard/operators/hitl.py` (modified, +25/-2)
- `providers/standard/tests/unit/standard/operators/test_hitl.py` (modified, +31/-4)

## Diff Summary (What the Fix Changes)

### `providers/standard/src/airflow/providers/standard/example_dags/example_hitl_operator.py`
```diff
@@ -118,7 +118,7 @@ def notify(self, context: Context) -> None:
         subject="Please choose option to proceed: ",
         options=["option 7", "option 8", "option 9"],
         defaults=["option 7"],
-        execution_timeout=datetime.timedelta(seconds=1),
+        response_timeout=datetime.timedelta(seconds=1),
         notifiers=[hitl_request_callback],
         on_success_callback=hitl_success_callback,
         on_failure_callback=hitl_failure_callback,
@@ -136,7 +136,7 @@ def notify(self, context: Context) -> None:
         Timeout Option: {{ ti.xcom_pull(task_ids='wait_for_default_option')["chosen_options"] }}
         """,
         defaults="Reject",
-        execution_timeout=datetime.timedelta(minutes=5),
+        response_timeout=datetime.timedelta(minutes=5),
         notifiers=[hitl_request_callback],
         on_success_callback=hitl_success_callback,
         on_failure_callback=hitl_failure_callback,
```

### `providers/standard/src/airflow/providers/standard/operators/hitl.py`
```diff
@@ -17,14 +17,17 @@
 from __future__ import annotations
 
 import logging
+import warnings
 
+from airflow.exceptions import AirflowProviderDeprecationWarning
 from airflow.providers.common.compat.sdk import AirflowOptionalProviderFeatureException
 from airflow.providers.standard.version_compat import AIRFLOW_V_3_1_3_PLUS, AIRFLOW_V_3_1_PLUS
 
 if not AIRFLOW_V_3_1_PLUS:
     raise AirflowOptionalProviderFeatureException("Human in the loop functionality needs Airflow 3.1+.")
 
 from collections.abc import Collection, Mapping, Sequence
+from datetime import timedelta
 from typing import TYPE_CHECKING, Any
 from urllib.parse import ParseResult, urlencode, urlparse, urlunparse
 
@@ -55,6 +58,9 @@ class HITLOperator(BaseOperator):
     :param params: dictionary of parameter definitions that are in the format of Dag params such that
         a Form Field can be rendered. Entered data is validated (schema, required fields) like for a Dag run
         and added to XCom of the task result.
+    :param response_timeout: Maximum time to wait for a human response after deferring to the trigger.
+        This is separate from ``execution_timeout`` which controls the pre-defer execution phase.
+        If not set, no timeout is applied to the human response wait.
     """
 
     template_fields: Collection[str] = ("subject", "body")
@@ -70,9 +76,26 @@ def __init__(
         params: ParamsDict | dict[str, Any] | None = None,
         notifiers: Sequence[BaseNotifier] | BaseNotifier | None = None,
         assigned_users: HITLUser | list[HITLUser] | None = None,
+        response_timeout: timedelta | None = None,
         **kwargs,
     ) -> None:
         super().__init__(**kwargs)
+
+        # Handle backward compatibility: if execution_timeout is set but response_timeout is not,
+        # migrate execution_timeout to response_timeout and clear it to prevent the BaseOperator
+        # timeout from racing the defer() call.
+        if self.execution_timeout and not response_tim
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `providers/standard/src/airflow/providers/standard/example_dags/example_hitl_operator.py`
- `providers/standard/src/airflow/providers/standard/operators/hitl.py`
