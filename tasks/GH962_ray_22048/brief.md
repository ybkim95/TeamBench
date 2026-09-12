# GH962_ray_22048: PoolActor now uses num_cpus=0 to avoid any deadlock (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest python/ray/tests/test_multiprocessing.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
