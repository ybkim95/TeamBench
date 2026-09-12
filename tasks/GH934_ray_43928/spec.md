# GH934_ray_43928: [serve] fix num replicas auto bug — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/ray-project/ray/issues/43929
- Repo: https://github.com/ray-project/ray

## Issue Description

### What happened + What you expected to happen

When only `num_replicas="auto"` is set in a Serve config yaml (without any overriding from `autoscaling_config`), deploying the config through Serve's rest api fails.

### Versions / Dependencies

master 52e1237cbf75bf1ae3b4639598f93bc6245bcb60

### Reproduction script

Deploy yaml:
```
applications:
  - name: default
    import_path: hello:app
    deployments:
      - name: f
        num_replicas: auto
```

Receive errors in controller logs:
```
(ServeController pid=36912) ERROR 2024-03-12 15:20:22,969 controller 36912 controller.py:404 - Exception updating deployment state.
(ServeController pid=36912) Traceback (most recent call last):
(ServeController pid=36912)   File "/Users/cindyz/ray/python/ray/serve/_private/controller.py", line 390, in run_control_loop
(ServeController pid=36912)     any_recovering = self.deployment_state_manager.update()
(ServeController pid=36912)   File "/Users/cindyz/ray/python/ray/serve/_private/deployment_state.py", line 2710, in update
(ServeController pid=36912)     deployment_state.check_and_update_replicas()
(ServeController pid=36912)   File "/Users/cindyz/ray/python/ray/serve/_private/deployment_state.py", line 2134, in check_and_update_replicas
(ServeController pid=36912)     slow_start = self._check_startup_replicas(ReplicaState.STARTING)
(ServeController pid=36912)   File "/Users/cindyz/ray/python/ray/serve/_private/deployment_state.py", line 2049, in _check_startup_replicas
(ServeController pid=36912)     self._target_state.target_num_replicas * 3,
(ServeController pid=36912) TypeError: unsupported operand type(s) for *: 'NoneType' and 'int'
```

### Issue Severity

None

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Reopening until cherry pick

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
