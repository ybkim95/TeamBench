# GH952_plotly.py_2445: Fix FigureWidget attribute error on wildcard import with ipywidgets not installed — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/plotly/plotly.py

## PR Description

Fixes the regression in 4.7.0 reported in https://github.com/plotly/plotly.py/issues/2443.  Also takes care of https://github.com/plotly/plotly.py/issues/1111 by producing a more informative error message.

The problem is that with Python 3.7+, we add `"FigureWidget"` to the `__all__` list in the `plotly.graph_objs`/`plotly.graph_objects` modules regardless of whether `ipywidgets` is installed.  But when `FigureWidget` is lazily imported, an exception is raised if a supported version of `ipywidgets` is not installed.  This results in the reported error when a user, or library, calls `from plotly.graph_objs import *`.

One option would be to check for the proper version of `ipywidgets` when `plotly.graph_objs` is imported and only add `FigureWidget` to `__all__` if it is found. But this results in a performance hit on every import of `plotly.graph_objs`, whether or not `FigureWidget` is used.

Another option would be to always allow `FigureWidget` to be imported, but raise an exception when a user tries to construct a `FigureWidget` if `ipywidgets` is not found.  Unfortunately, this isn't possible because `ipywidgets` is required in order to define the `FigureWidget` class itself so we can't import it without `ipywidgets`.

Instead, this PR introduces a new `plotly.missing_ipywidgets.FigureWidget` class. This class is a subclass of `BaseFigure` (just like the standard `Figure`), but all it does is raise an informative exception in the constructor informing the user that they need to install `ipywidgets` in order to use `FigureWidget`.  With this approach, `"FigureWidget"` is still always added to `__all__`, but on lazy import we check whether `ipywidgets` is installed. If it is, the current `plotly.graph_objs._figurewidget.FigureWidget` class is returned, otherwise the new `plotly.missing_ipywidgets.FigureWidget` class is returned.

Tests added in `plotly/tests/test_core/test_figure_widget_backend/test_missing_ipywigets.py`.

## Code PR
- [x] I have read through the [contributing notes](https://github.com/plotly/plotly.py/blob/master/contributing.md) and understand the structure of the package. In particular, if my PR modifies code of `plotly.graph_objects`, my modifications concern the `codegen` files and not generated files.
- [x] I have added tests (if submitting a new feature or correcting a bug) or
  modified existing tests.
- [x] I have added a CHANGELOG entry if fixing/changing/adding anything substantial.

## PR Review Comments

**[user]** on `packages/python/plotly/plotly/missing_ipywidgets.py`:

why even bother subclassing `BaseFigure` here? :)

**[user]** on `packages/python/plotly/plotly/missing_ipywidgets.py`:

It seemed safer to me for it to still pass `isinstance(fig, BaseFigure)` checks, but it probably doesn't make a difference.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
