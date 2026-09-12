# GH985_ray_22113: Fixed MRO for `DerivedActorClass` (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest python/ray/tests/test_actor.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
