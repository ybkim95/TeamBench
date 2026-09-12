# GH1002_scipy_24753: BUG: Rotation.apply read-only memoryview support (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest scipy/spatial/transform/tests/test_rotation.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
