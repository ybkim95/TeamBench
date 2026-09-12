# GH1155_matplotlib_30746: Fix PDF bloat for off-axis scatter with per-point colors (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest lib/matplotlib/tests/test_backend_pdf.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
