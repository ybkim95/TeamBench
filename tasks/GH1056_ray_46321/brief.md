# GH1056_ray_46321: [RLlib] Moving sampling coordination for `batch_mode=complete_episodes` to `synchronous_parallel_sample`. (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest rllib/algorithms/tests/test_callbacks_on_env_runner.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
