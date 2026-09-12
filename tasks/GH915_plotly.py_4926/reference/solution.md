# Reference solution — GH915_plotly.py_4926

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH915_plotly.py_4926`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH915_plotly.py_4926/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `packages/python/plotly/_plotly_utils/basevalidators.py` (modified, +29/-29)
- `packages/python/plotly/_plotly_utils/tests/validators/test_fig_deepcopy.py` (added, +38/-0)

## Diff Summary (What the Fix Changes)

### `packages/python/plotly/_plotly_utils/basevalidators.py`
```diff
@@ -223,6 +223,17 @@ def type_str(v):
     return "'{module}.{name}'".format(module=v.__module__, name=v.__name__)
 
 
+def is_typed_array_spec(v):
+    """
+    Return whether a value is considered to be a typed array spec for plotly.js
+    """
+    return isinstance(v, dict) and "bdata" in v and "dtype" in v
+
+
+def is_none_or_typed_array_spec(v):
+    return v is None or is_typed_array_spec(v)
+
+
 # Validators
 # ----------
 class BaseValidator(object):
@@ -393,8 +404,7 @@ def description(self):
 
     def validate_coerce(self, v):
 
-        if v is None:
-            # Pass None through
+        if is_none_or_typed_array_spec(v):
             pass
         elif is_homogeneous_array(v):
             v = copy_to_readonly_numpy_array(v)
@@ -591,8 +601,7 @@ def in_values(self, e):
         return False
 
     def validate_coerce(self, v):
-        if v is None:
-            # Pass None through
+        if is_none_or_typed_array_spec(v):
             pass
         elif self.array_ok and is_array(v):
             v_replaced = [self.perform_replacemenet(v_el) for v_el in v]
@@ -636,8 +645,7 @@ def description(self):
         )
 
     def validate_coerce(self, v):
-        if v is None:
-            # Pass None through
+        if is_none_or_typed_array_spec(v):
             pass
         elif not isinstance(v, bool):
             self.raise_invalid_val(v)
@@ -661,8 +669,7 @@ def description(self):
         )
 
     def validate_coerce(self, v):
-        if v is None:
-            # Pass None through
+        if is_none_or_typed_array_spec(v):
             pass
         elif isinstance(v, str):
             pass
@@ -752,8 +759,7 @@ def description(self):
         return desc
 
     def validate_coerce(self, v):
-        if v is None:
-            # Pass None through
+        if is_none_or_typed_array_spec(v):
             pass
         elif self.array_ok and is_homogeneous_array(v):
             np = get_module("numpy")
@@ -899,8 +905,7 @@ def description(self):
   
```

## Moved from `brief.md`

## Files That May Need Changes

- `packages/python/plotly/_plotly_utils/basevalidators.py`
