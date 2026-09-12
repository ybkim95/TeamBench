# Reference solution — GH1043_plotly.py_5415

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1043_plotly.py_5415`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1043_plotly.py_5415/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `_plotly_utils/basevalidators.py` (modified, +16/-2)
- `tests/test_optional/test_graph_objs/test_numpy.py` (added, +16/-0)

## Diff Summary (What the Fix Changes)

### `_plotly_utils/basevalidators.py`
```diff
@@ -22,6 +22,20 @@ def fullmatch(regex, string, flags=0):
     return re.match("(?:" + regex_string + r")\Z", string, flags=flags)
 
 
+def to_non_numpy_type(np, v):
+    """
+    Convert a numpy scalar value to a native Python type.
+    Calling .item() on a datetime64[ns] value returns an integer, since
+    Python datetimes only support microsecond precision. So we cast
+    datetime64[ns] to datetime64[us] to ensure it remains a datetime.
+
+    Should only be used in contexts where we already know `np` is defined.
+    """
+    if hasattr(v, "dtype") and v.dtype == np.dtype("datetime64[ns]"):
+        return v.astype("datetime64[us]").item()
+    return v.item()
+
+
 # Utility functions
 # -----------------
 def to_scalar_or_list(v):
@@ -35,12 +49,12 @@ def to_scalar_or_list(v):
     np = get_module("numpy", should_load=False)
     pd = get_module("pandas", should_load=False)
     if np and np.isscalar(v) and hasattr(v, "item"):
-        return v.item()
+        return to_non_numpy_type(np, v)
     if isinstance(v, (list, tuple)):
         return [to_scalar_or_list(e) for e in v]
     elif np and isinstance(v, np.ndarray):
         if v.ndim == 0:
-            return v.item()
+            return to_non_numpy_type(np, v)
         return [to_scalar_or_list(e) for e in v]
     elif pd and isinstance(v, (pd.Series, pd.Index)):
         return [to_scalar_or_list(e) for e in v]
```

## Moved from `brief.md`

## Files That May Need Changes

- `_plotly_utils/basevalidators.py`
