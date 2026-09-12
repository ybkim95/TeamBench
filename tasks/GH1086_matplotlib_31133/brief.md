# GH1086_matplotlib_31133: fix: resolve FigureCanvasTkAgg clipping on Windows HiDPI (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest lib/matplotlib/tests/test_backend_tk.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
