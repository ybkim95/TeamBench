# GH886_plotly.py_5258: Fix issue with default renderer when `ipython` is installed — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/plotly/plotly.py/issues/5257
- Repo: https://github.com/plotly/plotly.py

## Issue Description

- If the `ipython` package is installed in the environment, the default renderer (`pio.renderers.default`) is set to `"plotly_mimetype+notebook"` _even when running in a normal Python script_.
- This causes undesirable behavior for `fig.show()`: Calling `fig.show()` causes HTML/Javascript output to be printed to the terminal, rather than launching a browser window to show the plot. 
- If `ipython` is NOT installed, then `pio.renderers.default` is set to `"browser"`, as it should be, and `fig.show()` behaves normally.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
