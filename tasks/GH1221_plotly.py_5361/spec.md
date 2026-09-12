# GH1221_plotly.py_5361: Fix matplotlib import (pt.2) — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/plotly/plotly.py

## PR Description

Follow-on to (withheld: the upstream fix is not part of the task); one more broken import snuck in due to another PR being merged.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
