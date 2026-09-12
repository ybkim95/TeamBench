# Reference solution — GH1107_plotly.py_5535

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1107_plotly.py_5535`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1107_plotly.py_5535/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `plotly/express/_core.py` (modified, +2/-1)
- `tests/test_optional/test_px/test_px_functions.py` (modified, +10/-0)

## Diff Summary (What the Fix Changes)

### `plotly/express/_core.py`
```diff
@@ -588,7 +588,8 @@ def make_trace_kwargs(args, trace_spec, trace_data, mapping_labels, sizeref):
             and attr_name == "z"
         ):
             # ensure that stuff like "count" gets into the hoverlabel
-            mapping_labels[attr_label] = "%%{%s}" % attr_name
+            if attr_label is not None:
+                mapping_labels[attr_label] = "%%{%s}" % attr_name
     if trace_spec.constructor not in [go.Parcoords, go.Parcats]:
         # Modify mapping_labels according to hover_data keys
         # if hover_data is a dict
```

## Moved from `brief.md`

## Files That May Need Changes

- `plotly/express/_core.py`
