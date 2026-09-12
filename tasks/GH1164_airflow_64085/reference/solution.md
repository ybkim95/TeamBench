# Reference solution — GH1164_airflow_64085

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1164_airflow_64085`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1164_airflow_64085/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `providers/amazon/src/airflow/providers/amazon/aws/operators/dms.py` (modified, +31/-5)
- `providers/amazon/src/airflow/providers/amazon/aws/operators/emr.py` (modified, +19/-16)
- `providers/amazon/src/airflow/providers/amazon/aws/operators/neptune.py` (modified, +13/-14)
- `providers/amazon/src/airflow/providers/amazon/aws/sensors/mwaa.py` (modified, +9/-2)
- `providers/amazon/src/airflow/providers/amazon/aws/triggers/base.py` (modified, +15/-10)
- `providers/amazon/src/airflow/providers/amazon/aws/triggers/dms.py` (modified, +1/-1)
- `providers/amazon/src/airflow/providers/amazon/aws/triggers/glue.py` (modified, +1/-1)
- `providers/amazon/tests/unit/amazon/aws/operators/test_dms.py` (modified, +51/-0)
- `providers/amazon/tests/unit/amazon/aws/operators/test_emr_serverless.py` (modified, +20/-0)
- `providers/amazon/tests/unit/amazon/aws/sensors/test_mwaa.py` (modified, +22/-0)
- `providers/amazon/tests/unit/amazon/aws/triggers/test_base.py` (modified, +19/-0)
- `providers/amazon/tests/unit/amazon/aws/triggers/test_glue.py` (modified, +4/-3)
- `providers/amazon/tests/unit/amazon/aws/triggers/test_neptune.py` (modified, +3/-3)

## Diff Summary (What the Fix Changes)

### `providers/amazon/src/airflow/providers/amazon/aws/operators/dms.py`
```diff
@@ -30,6 +30,7 @@
     DmsReplicationStoppedTrigger,
     DmsReplicationTerminalStatusTrigger,
 )
+from airflow.providers.amazon.aws.utils import validate_execute_complete_event
 from airflow.providers.amazon.aws.utils.mixins import aws_template_fields
 from airflow.providers.common.compat.sdk import AirflowException, Context, conf
 
@@ -510,11 +511,21 @@ def handle_delete_wait(self):
                 self.log.info("DMS replication config(%s) deleted.", self.replication_config_arn)
 
     def execute_complete(self, context, event=None):
-        self.replication_config_arn = event.get("replication_config_arn")
+        validated_event = validate_execute_complete_event(event)
+
+        if validated_event["status"] != "success":
+            raise AirflowException(f"Error deleting DMS replication config: {validated_event}")
+
+        self.replication_config_arn = validated_event.get("replication_config_arn")
         self.log.info("DMS replication config(%s) deleted.", self.replication_config_arn)
 
     def retry_execution(self, context, event=None):
-        self.replication_config_arn = event.get("replication_config_arn")
+        validated_event = validate_execute_complete_event(event)
+
+        if validated_event["status"] != "success":
+            raise AirflowException(f"Error waiting for DMS replication config: {validated_event}")
+
+        self.replication_config_arn = validated_event.get("replication_config_arn")
         self.log.info("Retrying replication config(%s) deletion.", self.replication_config_arn)
         self.execute(context)
 
@@ -703,11 +714,21 @@ def execute(self, context: Context):
             self.log.info("Status: %s Provision status: %s", current_status, provision_status)
 
     def execute_complete(self, context, event=None):
-        self.replication_config_arn = event.get("replication_config_arn")
+        validated_event = validate_execute_complete_event(event)
+
+        if validated_event["status"] != "success":
+            r
```

### `providers/amazon/src/airflow/providers/amazon/aws/operators/emr.py`
```diff
@@ -1620,24 +1620,26 @@ def stop_application(self, context: Context, event: dict[str, Any] | None = None
         if event is None:
             self.log.error("Trigger error: event is None")
             raise AirflowException("Trigger error: event is None")
-        if event["status"] == "success":
-            self.hook.conn.stop_application(applicationId=self.application_id)
-            self.defer(
-                trigger=EmrServerlessStopApplicationTrigger(
-                    application_id=self.application_id,
-                    aws_conn_id=self.aws_conn_id,
-                    waiter_delay=self.waiter_delay,
-                    waiter_max_attempts=self.waiter_max_attempts,
-                ),
-                timeout=timedelta(seconds=self.waiter_max_attempts * self.waiter_delay),
-                method_name="execute_complete",
-            )
+        if event["status"] != "success":
+            raise AirflowException(f"Error cancelling EMR Serverless jobs: {event}")
+        self.hook.conn.stop_application(applicationId=self.application_id)
+        self.defer(
+            trigger=EmrServerlessStopApplicationTrigger(
+                application_id=self.application_id,
+                aws_conn_id=self.aws_conn_id,
+                waiter_delay=self.waiter_delay,
+                waiter_max_attempts=self.waiter_max_attempts,
+            ),
+            timeout=timedelta(seconds=self.waiter_max_attempts * self.waiter_delay),
+            method_name="execute_complete",
+        )
 
     def execute_complete(self, context: Context, event: dict[str, Any] | None = None) -> None:
         validated_event = validate_execute_complete_event(event)
 
-        if validated_event["status"] == "success":
-            self.log.info("EMR serverless application %s stopped successfully", self.application_id)
+        if validated_event["status"] != "success":
+            raise AirflowException(f"Error stopping EMR Serverless application: {validated_event}")
+  
```

### `providers/amazon/src/airflow/providers/amazon/aws/operators/neptune.py`
```diff
@@ -29,6 +29,7 @@
     NeptuneClusterInstancesAvailableTrigger,
     NeptuneClusterStoppedTrigger,
 )
+from airflow.providers.amazon.aws.utils import validate_execute_complete_event
 from airflow.providers.amazon.aws.utils.mixins import aws_template_fields
 from airflow.providers.common.compat.sdk import AirflowException, conf
 
@@ -187,14 +188,13 @@ def execute(self, context: Context, event: dict[str, Any] | None = None, **kwarg
         return {"db_cluster_id": self.cluster_id}
 
     def execute_complete(self, context: Context, event: dict[str, Any] | None = None) -> dict[str, str]:
-        status = ""
-        cluster_id = ""
+        validated_event = validate_execute_complete_event(event)
 
-        if event:
-            status = event.get("status", "")
-            cluster_id = event.get("cluster_id", "")
+        if validated_event["status"] != "success":
+            raise AirflowException(f"Error starting Neptune cluster: {validated_event}")
 
-        self.log.info("Neptune cluster %s available with status: %s", cluster_id, status)
+        cluster_id = validated_event.get("db_cluster_id", "")
+        self.log.info("Neptune cluster %s available with status: %s", cluster_id, validated_event["status"])
 
         return {"db_cluster_id": cluster_id}
 
@@ -314,13 +314,12 @@ def execute(self, context: Context, event: dict[str, Any] | None = None, **kwarg
         return {"db_cluster_id": self.cluster_id}
 
     def execute_complete(self, context: Context, event: dict[str, Any] | None = None) -> dict[str, str]:
-        status = ""
-        cluster_id = ""
-        self.log.info(event)
-        if event:
-            status = event.get("status", "")
-            cluster_id = event.get("cluster_id", "")
-
-        self.log.info("Neptune cluster %s stopped with status: %s", cluster_id, status)
+        validated_event = validate_execute_complete_event(event)
+
+        if validated_event["status"] != "success":
+            raise AirflowException(f"Error stop
```

### `providers/amazon/src/airflow/providers/amazon/aws/sensors/mwaa.py`
```diff
@@ -23,6 +23,7 @@
 from airflow.providers.amazon.aws.hooks.mwaa import MwaaHook
 from airflow.providers.amazon.aws.sensors.base_aws import AwsBaseSensor
 from airflow.providers.amazon.aws.triggers.mwaa import MwaaDagRunCompletedTrigger, MwaaTaskCompletedTrigger
+from airflow.providers.amazon.aws.utils import validate_execute_complete_event
 from airflow.providers.amazon.aws.utils.mixins import aws_template_fields
 from airflow.providers.common.compat.sdk import AirflowException, conf
 from airflow.utils.state import DagRunState, TaskInstanceState
@@ -143,7 +144,10 @@ def poke(self, context: Context) -> bool:
         return state in self.success_states
 
     def execute_complete(self, context: Context, event: dict[str, Any] | None = None) -> None:
-        return None
+        validated_event = validate_execute_complete_event(event)
+
+        if validated_event["status"] != "success":
+            raise AirflowException(f"Error in MWAA DAG run: {validated_event}")
 
     def execute(self, context: Context):
         if self.deferrable:
@@ -281,7 +285,10 @@ def poke(self, context: Context) -> bool:
         return state in self.success_states
 
     def execute_complete(self, context: Context, event: dict[str, Any] | None = None) -> None:
-        return None
+        validated_event = validate_execute_complete_event(event)
+
+        if validated_event["status"] != "success":
+            raise AirflowException(f"Error in MWAA task: {validated_event}")
 
     def execute(self, context: Context):
         if self.external_dag_run_id is None:
```

### `providers/amazon/src/airflow/providers/amazon/aws/triggers/base.py`
```diff
@@ -21,6 +21,7 @@
 from collections.abc import AsyncIterator
 from typing import TYPE_CHECKING, Any
 
+from airflow.exceptions import AirflowException
 from airflow.providers.amazon.aws.utils.waiter_with_logging import async_wait
 from airflow.triggers.base import BaseTrigger, TriggerEvent
 from airflow.utils.helpers import prune_dict
@@ -149,13 +150,17 @@ async def run(self) -> AsyncIterator[TriggerEvent]:
                 client=client,
                 config_overrides=self.waiter_config_overrides,
             )
-            await async_wait(
-                waiter,
-                self.waiter_delay,
-                self.attempts,
-                self.waiter_args,
-                self.failure_message,
-                self.status_message,
-                self.status_queries,
-            )
-            yield TriggerEvent({"status": "success", self.return_key: self.return_value})
+            try:
+                await async_wait(
+                    waiter,
+                    self.waiter_delay,
+                    self.attempts,
+                    self.waiter_args,
+                    self.failure_message,
+                    self.status_message,
+                    self.status_queries,
+                )
+            except AirflowException as e:
+                yield TriggerEvent({"status": "error", "message": str(e), self.return_key: self.return_value})
+            else:
+                yield TriggerEvent({"status": "success", self.return_key: self.return_value})
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `providers/amazon/src/airflow/providers/amazon/aws/operators/dms.py`
- `providers/amazon/src/airflow/providers/amazon/aws/operators/emr.py`
- `providers/amazon/src/airflow/providers/amazon/aws/operators/neptune.py`
- `providers/amazon/src/airflow/providers/amazon/aws/sensors/mwaa.py`
- `providers/amazon/src/airflow/providers/amazon/aws/triggers/base.py`
