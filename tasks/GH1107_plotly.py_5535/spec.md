# GH1107_plotly.py_5535: fix: handle empty px.histogram() by skipping None label in hover template — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/plotly/plotly.py/issues/5534
- Repo: https://github.com/plotly/plotly.py

## Issue Description

Creating an empty histogram with px.histogram() leads to a TypeError. Other types of graphs like px.pie(), px.scatter(), px.bar() allow empty figure to be created.

### Steps to reproduce

```
import plotly.express as px
px.scatter()  # this is fine
px. histogram()  # this is not
```

### Notes

Plotly 6.6

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
