# Reference solution — GH1044_plotly.py_5193

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1044_plotly.py_5193`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1044_plotly.py_5193/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `plotly/basedatatypes.py` (modified, +1/-1)
- `tests/test_optional/test_kaleido/test_kaleido.py` (modified, +45/-2)

## Diff Summary (What the Fix Changes)

### `plotly/basedatatypes.py`
```diff
@@ -3908,7 +3908,7 @@ def write_image(self, *args, **kwargs):
                 warnings.warn(
                     ENGINE_PARAM_DEPRECATION_MSG, DeprecationWarning, stacklevel=2
                 )
-            return pio.write_image(self, *args, **kwargs)
+        return pio.write_image(self, *args, **kwargs)
 
     # Static helpers
     # --------------
```

## Moved from `brief.md`

## Files That May Need Changes

- `plotly/basedatatypes.py`
