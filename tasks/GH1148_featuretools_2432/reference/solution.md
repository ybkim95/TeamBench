# Reference solution — GH1148_featuretools_2432

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1148_featuretools_2432`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1148_featuretools_2432/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/source/release_notes.rst` (modified, +1/-0)
- `featuretools/primitives/utils.py` (modified, +7/-0)
- `featuretools/tests/primitive_tests/test_feature_serialization.py` (modified, +20/-0)
- `featuretools/tests/primitive_tests/test_features_deserializer.py` (modified, +28/-0)

## Diff Summary (What the Fix Changes)

### `featuretools/primitives/utils.py`
```diff
@@ -8,6 +8,7 @@
 from woodwork.column_schema import ColumnSchema
 
 import featuretools
+from featuretools.primitives import NumberOfCommonWords
 from featuretools.primitives.base import (
     AggregationPrimitive,
     PrimitiveBase,
@@ -343,6 +344,8 @@ def serialize_primitive(primitive):
     """build a dictionary with the data necessary to construct the given primitive"""
     args_dict = {name: val for name, val in primitive.get_arguments()}
     cls = type(primitive)
+    if cls == NumberOfCommonWords and "word_set" in args_dict:
+        args_dict["word_set"] = list(args_dict["word_set"])
     return {
         "type": cls.__name__,
         "module": cls.__module__,
@@ -385,6 +388,10 @@ def deserialize_primitive(self, primitive_dict):
                 'Primitive "%s" in module "%s" not found' % (class_name, module_name),
             )
         arguments = primitive_dict["arguments"]
+        if cls == NumberOfCommonWords and "word_set" in arguments:
+            # We converted word_set from a set to a list to make it serializable,
+            # we should convert it back now.
+            arguments["word_set"] = set(arguments["word_set"])
         primitive_instance = cls(**arguments)
 
         return primitive_instance
```

## Moved from `brief.md`

## Files That May Need Changes

- `featuretools/primitives/utils.py`
