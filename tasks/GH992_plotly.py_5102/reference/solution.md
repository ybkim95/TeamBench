# Reference solution — GH992_plotly.py_5102

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH992_plotly.py_5102`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH992_plotly.py_5102/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CHANGELOG.md` (modified, +5/-0)
- `plotly/basewidget.py` (modified, +5/-0)
- `tests/test_core/test_figure_widget_backend/test_validate_initialization.py` (added, +21/-0)

## Diff Summary (What the Fix Changes)

### `plotly/basewidget.py`
```diff
@@ -142,6 +142,11 @@ def __init__(
         # views of this widget
         self._view_count = 0
 
+        # Initialize widget layout and data for third-party widget integration
+        # --------------------------------------------------------------------
+        self._widget_layout = deepcopy(self._layout_obj._props)
+        self._widget_data = deepcopy(self._data)
+
     def show(self, *args, **kwargs):
         return self
 
```

## Moved from `brief.md`

## Files That May Need Changes

- `plotly/basewidget.py`
