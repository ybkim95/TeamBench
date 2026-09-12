# GH1154_matplotlib_30795: Fix array alpha to multiply (not replace) existing RGBA alpha (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest lib/matplotlib/tests/test_image.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
