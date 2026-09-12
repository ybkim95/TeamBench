# Reference solution — GH938_airflow_64087

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH938_airflow_64087`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH938_airflow_64087/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `airflow-core/src/airflow/models/dagrun.py` (modified, +1/-1)
- `airflow-core/tests/unit/models/test_dagrun.py` (modified, +39/-0)

## Diff Summary (What the Fix Changes)

### `airflow-core/src/airflow/models/dagrun.py`
```diff
@@ -1020,7 +1020,7 @@ def is_effective_leaf(task):
         return leaf_tis
 
     def _emit_dagrun_span(self, state: DagRunState):
-        ctx = TraceContextTextMapPropagator().extract(self.context_carrier)
+        ctx = TraceContextTextMapPropagator().extract(self.context_carrier or {})
         span = trace.get_current_span(context=ctx)
         span_context = span.get_span_context()
         with override_ids(span_context.trace_id, span_context.span_id):
```

## Moved from `brief.md`

## Files That May Need Changes

- `airflow-core/src/airflow/models/dagrun.py`
