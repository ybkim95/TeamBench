# Reference solution — GH1172_plotly.py_5000

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1172_plotly.py_5000`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1172_plotly.py_5000/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `packages/python/plotly/plotly/express/_core.py` (modified, +5/-3)
- `packages/python/plotly/plotly/tests/test_optional/test_px/test_px_functions.py` (modified, +33/-0)

## Diff Summary (What the Fix Changes)

### `packages/python/plotly/plotly/express/_core.py`
```diff
@@ -2147,6 +2147,8 @@ def process_dataframe_timeline(args):
 
 
 def process_dataframe_pie(args, trace_patch):
+    import numpy as np
+
     names = args.get("names")
     if names is None:
         return args, trace_patch
@@ -2159,12 +2161,12 @@ def process_dataframe_pie(args, trace_patch):
     uniques = df.get_column(names).unique(maintain_order=True).to_list()
     order = [x for x in OrderedDict.fromkeys(list(order_in) + uniques) if x in uniques]
 
-    # Sort args['data_frame'] by column 'b' according to order `order`.
+    # Sort args['data_frame'] by column `names` according to order `order`.
     token = nw.generate_temporary_column_name(8, df.columns)
     args["data_frame"] = (
         df.with_columns(
-            nw.col("b")
-            .replace_strict(order, range(len(order)), return_dtype=nw.UInt32)
+            nw.col(names)
+            .replace_strict(order, np.arange(len(order)), return_dtype=nw.UInt32)
             .alias(token)
         )
         .sort(token)
```

## Moved from `brief.md`

## Files That May Need Changes

- `packages/python/plotly/plotly/express/_core.py`
