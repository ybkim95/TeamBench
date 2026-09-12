# GH993_plotly.py_4914: fix: px.timeline was raising when x_start and/or x_end were already datetime for Polars / PyArrow (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest packages/python/plotly/plotly/tests/test_optional/test_px/test_px_functions.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
