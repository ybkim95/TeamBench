# Reference solution — GH1066_matplotlib_31315

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1066_matplotlib_31315`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1066_matplotlib_31315/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `lib/matplotlib/legend.py` (modified, +5/-0)
- `lib/matplotlib/tests/test_legend.py` (modified, +10/-1)

## Diff Summary (What the Fix Changes)

### `lib/matplotlib/legend.py`
```diff
@@ -1385,6 +1385,11 @@ def _parse_legend_args(axs, *args, handles=None, labels=None, **kwargs):
 
     elif len(args) == 2:  # 2 args: user defined handles and labels.
         handles, labels = args[:2]
+        if (hasattr(handles, "__len__") and hasattr(labels, "__len__")
+                and len(handles) != len(labels)):
+            _api.warn_external(f"Mismatched number of handles and labels: "
+                               f"len(handles) = {len(handles)} "
+                               f"len(labels) = {len(labels)}")
 
     else:
         raise _api.nargs_error('legend', '0-2', len(args))
```

## Moved from `brief.md`

## Files That May Need Changes

- `lib/matplotlib/legend.py`
