# Reference solution — GH886_plotly.py_5258

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH886_plotly.py_5258`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH886_plotly.py_5258/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `plotly/io/_renderers.py` (modified, +1/-1)
- `tests/test_io/test_renderers.py` (modified, +7/-0)

## Diff Summary (What the Fix Changes)

### `plotly/io/_renderers.py`
```diff
@@ -485,7 +485,7 @@ def show(fig, renderer=None, validate=True, **kwargs):
         )
 
     default_renderer = env_renderer
-elif ipython:
+elif ipython and ipython.get_ipython():
     # Try to detect environment so that we can enable a useful
     # default renderer
     if not default_renderer:
```

## Moved from `brief.md`

## Files That May Need Changes

- `plotly/io/_renderers.py`
