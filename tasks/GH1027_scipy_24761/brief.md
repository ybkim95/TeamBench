# GH1027_scipy_24761: BUG: `from_rotvec` read-only support (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest scipy/spatial/transform/tests/test_rotation.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
