# GH1033_ray_23187: `map` and `map_unordered` cancel previous tasks before submitting new ones (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest python/ray/tests/test_actor_pool.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
