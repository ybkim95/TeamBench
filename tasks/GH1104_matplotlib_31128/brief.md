# GH1104_matplotlib_31128: Fix relim() ignoring scatter PathCollection offsets (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest lib/matplotlib/tests/test_axes.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
