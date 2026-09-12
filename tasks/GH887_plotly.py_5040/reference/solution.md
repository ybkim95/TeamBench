# Reference solution — GH887_plotly.py_5040

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH887_plotly.py_5040`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH887_plotly.py_5040/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CHANGELOG.md` (modified, +5/-0)
- `plotly/io/_json.py` (modified, +1/-1)
- `tests/test_io/test_to_from_plotly_json.py` (modified, +6/-0)

## Diff Summary (What the Fix Changes)

### `plotly/io/_json.py`
```diff
@@ -529,7 +529,7 @@ def clean_to_json_compatible(obj, **kwargs):
 
     # pandas
     if pd is not None:
-        if obj is pd.NaT:
+        if obj is pd.NaT or obj is pd.NA:
             return None
         elif isinstance(obj, (pd.Series, pd.DatetimeIndex)):
             if numpy_allowed and obj.dtype.kind in ("b", "i", "u", "f"):
```

## Moved from `brief.md`

## Files That May Need Changes

- `plotly/io/_json.py`
