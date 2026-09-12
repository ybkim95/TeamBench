# Reference solution — GH993_plotly.py_4914

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH993_plotly.py_4914`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH993_plotly.py_4914/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `packages/python/plotly/plotly/express/_core.py` (modified, +15/-10)
- `packages/python/plotly/plotly/tests/test_optional/test_px/test_px_functions.py` (modified, +26/-0)

## Diff Summary (What the Fix Changes)

### `packages/python/plotly/plotly/express/_core.py`
```diff
@@ -2121,16 +2121,21 @@ def process_dataframe_timeline(args):
     if args["x_start"] is None or args["x_end"] is None:
         raise ValueError("Both x_start and x_end are required")
 
-    try:
-        df: nw.DataFrame = args["data_frame"]
-        df = df.with_columns(
-            nw.col(args["x_start"]).str.to_datetime().alias(args["x_start"]),
-            nw.col(args["x_end"]).str.to_datetime().alias(args["x_end"]),
-        )
-    except Exception:
-        raise TypeError(
-            "Both x_start and x_end must refer to data convertible to datetimes."
-        )
+    df: nw.DataFrame = args["data_frame"]
+    schema = df.schema
+    to_convert_to_datetime = [
+        col
+        for col in [args["x_start"], args["x_end"]]
+        if schema[col] != nw.Datetime and schema[col] != nw.Date
+    ]
+
+    if to_convert_to_datetime:
+        try:
+            df = df.with_columns(nw.col(to_convert_to_datetime).str.to_datetime())
+        except Exception as exc:
+            raise TypeError(
+                "Both x_start and x_end must refer to data convertible to datetimes."
+            ) from exc
 
     # note that we are not adding any columns to the data frame here, so no risk of overwrite
     args["data_frame"] = df.with_columns(
```

## Moved from `brief.md`

## Files That May Need Changes

- `packages/python/plotly/plotly/express/_core.py`
