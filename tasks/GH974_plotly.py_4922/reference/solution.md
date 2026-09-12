# Reference solution — GH974_plotly.py_4922

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH974_plotly.py_4922`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH974_plotly.py_4922/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `packages/python/plotly/_plotly_utils/utils.py` (modified, +3/-1)
- `packages/python/plotly/plotly/tests/test_io/test_to_from_json.py` (modified, +14/-0)
- `packages/python/plotly/plotly/tests/test_optional/test_px/test_px.py` (modified, +15/-0)

## Diff Summary (What the Fix Changes)

### `packages/python/plotly/_plotly_utils/utils.py`
```diff
@@ -43,8 +43,10 @@ def to_typed_array_spec(v):
     """
     v = copy_to_readonly_numpy_array(v)
 
+    # Skip b64 encoding if numpy is not installed,
+    # or if v is not a numpy array, or if v is empty
     np = get_module("numpy", should_load=False)
-    if not np or not isinstance(v, np.ndarray):
+    if not np or not isinstance(v, np.ndarray) or v.size == 0:
         return v
 
     dtype = str(v.dtype)
```

## Moved from `brief.md`

## Files That May Need Changes

- `packages/python/plotly/_plotly_utils/utils.py`
