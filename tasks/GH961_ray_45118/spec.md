# GH961_ray_45118: [serve] Fix controller recovery bug — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/ray-project/ray

## PR Description

[serve] Fix controller recovery bug

When controller recovers and there are autoscaling deployments whose configs don't have `initial_replicas` set, controller recover fails because of this bug.

I've fixed the bug and added a test for it.

Signed-off-by: Cindy Zhang <[email redacted]>

## PR Review Comments

**[user]** on `python/ray/serve/tests/test_controller_recovery.py`:

Could you rewrite this as:

```python
@pytest.mark.parametrize("deployment_options", [
    {"num_replicas": 2},
    {"autoscaling_config": {"min_replicas": 2, "max_replicas": 2}},
])
```

That way, we don't need a conditional in the test (since we can pass this directly into the decorator with `**deployment_options`), and the fixture is more generalizable.

**[user]** on `python/ray/serve/_private/autoscaling_state.py`:

Do the callers of `register` handle a `None` return type gracefully?

**[user]** on `python/ray/serve/_private/autoscaling_state.py`:

Yeah only `deploy` uses the return value of `register_deployment() -> register()`, and that callsite is guaranteed to pass in a non-null num replicas

**[user]** on `python/ray/serve/_private/autoscaling_state.py`:

Could you update the return type of [`register_deployment`](https://github.com/ray-project/ray/blob/9a3b22b566119b6c2a1ce479c843e6a4414fd9e5/python/ray/serve/_private/autoscaling_state.py#L330-L335) since it can return `None` now?

**[user]** on `python/ray/serve/_private/autoscaling_state.py`:

Updated!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
