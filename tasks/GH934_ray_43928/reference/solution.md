# Reference solution — GH934_ray_43928

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH934_ray_43928`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH934_ray_43928/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `python/ray/serve/_private/application_state.py` (modified, +3/-2)
- `python/ray/serve/tests/test_deploy_2.py` (modified, +47/-3)
- `python/ray/serve/tests/test_deploy_app.py` (modified, +39/-2)

## Diff Summary (What the Fix Changes)

### `python/ray/serve/_private/application_state.py`
```diff
@@ -1057,16 +1057,17 @@ def override_deployment_info(
             ):
                 options["max_ongoing_requests"] = NEW_DEFAULT_MAX_ONGOING_REQUESTS
 
+            new_config = AutoscalingConfig.default().dict()
             # If `autoscaling_config` is specified, its values override
             # the default `num_replicas="auto"` configuration
             autoscaling_config = (
                 options.get("autoscaling_config")
                 or info.deployment_config.autoscaling_config
             )
             if autoscaling_config:
-                new_config = AutoscalingConfig.default().dict()
                 new_config.update(autoscaling_config)
-                options["autoscaling_config"] = AutoscalingConfig(**new_config)
+
+            options["autoscaling_config"] = AutoscalingConfig(**new_config)
 
         # What to pass to info.update
         override_options = dict()
```

## Moved from `brief.md`

## Files That May Need Changes

- `python/ray/serve/_private/application_state.py`
