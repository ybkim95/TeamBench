# GH974_plotly.py_4922: fix: Skip base64 conversion for empty arrays (fixes #4919) (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest packages/python/plotly/plotly/tests/test_io/test_to_from_json.py packages/python/plotly/plotly/tests/test_optional/test_px/test_px.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
