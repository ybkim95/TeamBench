# Reference solution — GH1185_airflow_62174

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1185_airflow_62174`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1185_airflow_62174/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `task-sdk/src/airflow/sdk/bases/decorator.py` (modified, +38/-0)
- `task-sdk/tests/task_sdk/bases/test_decorator.py` (modified, +146/-1)

## Diff Summary (What the Fix Changes)

### `task-sdk/src/airflow/sdk/bases/decorator.py`
```diff
@@ -313,6 +313,33 @@ def __init__(
             param.replace(default=None) if param.name in KNOWN_CONTEXT_KEYS else param
             for param in signature.parameters.values()
         ]
+
+        # Python requires that positional parameters with defaults don't precede those without.
+        # This only applies to POSITIONAL_ONLY and POSITIONAL_OR_KEYWORD parameters — *args,
+        # **kwargs, and keyword-only parameters follow different rules.
+        positional_kinds = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
+        positional = [(i, p) for i, p in enumerate(parameters) if p.kind in positional_kinds]
+        first_default_idx = next((i for i, p in positional if p.default != inspect.Parameter.empty), None)
+
+        # Names of non-context-key params that receive an injected None default purely to satisfy
+        # Python's ordering constraint. These params are still semantically required and must be
+        # explicitly provided via op_args/op_kwargs — we verify this below after bind().
+        injected_for_ordering: set[str] = set()
+        if first_default_idx is not None:
+            new_parameters = []
+            for i, param in enumerate(parameters):
+                if (
+                    i > first_default_idx
+                    and param.kind in positional_kinds
+                    and param.default == inspect.Parameter.empty
+                ):
+                    new_parameters.append(param.replace(default=None))
+                    if param.name not in KNOWN_CONTEXT_KEYS:
+                        injected_for_ordering.add(param.name)
+                else:
+                    new_parameters.append(param)
+            parameters = new_parameters
+
         try:
             signature = signature.replace(parameters=parameters)
         except ValueError as err:
@@ -342,6 +369,17 @@ def __init__(
         else:
             signature.bind(*op_args, **op_kwargs)
 
+        # Params in injected_fo
```

## Moved from `brief.md`

## Files That May Need Changes

- `task-sdk/src/airflow/sdk/bases/decorator.py`
