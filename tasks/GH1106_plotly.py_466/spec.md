# GH1106_plotly.py_466: Ensure plotlyjs loaded — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/plotly/plotly.py

## PR Description

Fixes issues with offline mode not working after refreshes.
### In Brief:
- Check the DOM for plotly.js rather than the global flag in python
- Load it on all offline notebook plot methods
- Clean up some unused code and deprecate `init_notebook_mode`

## PR Review Comments

**[user]** on `plotly/offline/offline.py`:

random comma

**[user]** on `plotly/offline/offline.py`:

:cow2: could use less escaping by following original formatting, but not needed!

**[user]** on `plotly/tests/test_optional/test_offline/test_offline.py`:

🎉

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
