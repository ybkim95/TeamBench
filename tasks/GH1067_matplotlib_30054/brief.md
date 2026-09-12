# GH1067_matplotlib_30054: Fixed an off-by-half-pixel bug in image resampling when using a nonaffine transform (e.g., a log axis) (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest lib/matplotlib/tests/test_image.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
