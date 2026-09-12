# GH1085_matplotlib_31313: Fixed lingering bugs with image rendering related to exact half display pixels (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest lib/matplotlib/tests/test_image.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
