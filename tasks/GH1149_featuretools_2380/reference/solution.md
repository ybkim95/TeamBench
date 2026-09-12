# Reference solution — GH1149_featuretools_2380

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1149_featuretools_2380`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1149_featuretools_2380/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/source/release_notes.rst` (modified, +1/-0)
- `featuretools/primitives/base/aggregation_primitive_base.py` (modified, +0/-6)
- `featuretools/primitives/base/primitive_base.py` (modified, +6/-0)
- `featuretools/synthesis/deep_feature_synthesis.py` (modified, +33/-19)
- `featuretools/synthesis/utils.py` (modified, +1/-1)
- `featuretools/tests/conftest.py` (modified, +24/-0)
- `featuretools/tests/primitive_tests/test_agg_feats.py` (modified, +1/-97)
- `featuretools/tests/primitive_tests/test_feature_base.py` (modified, +78/-0)
- `featuretools/tests/synthesis/test_deep_feature_synthesis.py` (modified, +56/-1)
- `featuretools/tests/testing_utils/__init__.py` (modified, +8/-7)
- `featuretools/tests/testing_utils/features.py` (modified, +9/-1)

## Diff Summary (What the Fix Changes)

### `featuretools/primitives/base/aggregation_primitive_base.py`
```diff
@@ -2,12 +2,6 @@
 
 
 class AggregationPrimitive(PrimitiveBase):
-    stack_on = None  # whitelist of primitives that can be in input_types
-    stack_on_exclude = None  # blacklist of primitives that can be in signature
-    base_of = None  # whitelist of primitives this primitive can be input for
-    base_of_exclude = None  # primitives this primitive can't be input for
-    stack_on_self = True  # determines if primitive can be in input_types for self
-
     def generate_name(
         self,
         base_feature_names,
```

### `featuretools/primitives/base/primitive_base.py`
```diff
@@ -32,6 +32,12 @@ class PrimitiveBase(object):
     base_of = None
     # blacklist of primitives can have this primitive in input_types
     base_of_exclude = None
+    # whitelist of primitives that can be in input_types
+    stack_on = None
+    # blacklist of primitives that can be in signature
+    stack_on_exclude = None
+    # determines if primitive can be in input_types for self
+    stack_on_self = True
     # (bool) If True will only make one feature per unique set of base features
     commutative = False
     #: (list): Additional compatible libraries
```

### `featuretools/synthesis/deep_feature_synthesis.py`
```diff
@@ -223,7 +223,6 @@ def __init__(
                 for p in primitives.get_default_aggregation_primitives()
                 if df_library in p.compatibility
             ]
-        self.agg_primitives = []
         self.agg_primitives = sorted(
             [
                 check_primitive(
@@ -702,10 +701,12 @@ def _build_transform_features(
                 trans_prim,
                 current_options,
                 require_direct_input=require_direct_input,
-                feature_filter=check_transform_stacking,
+                feature_filter=not_a_transform_input,
             )
 
             for matching_input in matching_inputs:
+                if not can_stack_primitive_on_inputs(trans_prim, matching_input):
+                    continue
                 if not any(
                     True for bf in matching_input if bf.number_output_features != 1
                 ):
@@ -727,7 +728,7 @@ def _build_transform_features(
                 input_types,
                 groupby_prim,
                 current_options,
-                feature_filter=check_transform_stacking,
+                feature_filter=not_a_transform_input,
             )
 
             # get columns to use as groupbys, use IDs as default unless other groupbys specified
@@ -754,6 +755,8 @@ def _build_transform_features(
             # groupby, and don't create features of inputs/groupbys which are
             # all direct features with the same relationship path
             for matching_input in matching_inputs:
+                if not can_stack_primitive_on_inputs(groupby_prim, matching_input):
+                    continue
                 if not any(
                     True for bf in matching_input if bf.number_output_features != 1
                 ):
@@ -849,7 +852,7 @@ def feature_filter(f):
             wheres = list(self.where_clauses[child_dataframe.ww.name])
 
             for matching_input in matching_inputs:
-                if not check_stacking(agg_prim, matching_i
```

### `featuretools/synthesis/utils.py`
```diff
@@ -59,4 +59,4 @@ def get_unused_primitives(specified, used):
         else primitive.name
         for primitive in specified
     }
-    return sorted(list(specified.difference(used)))
+    return sorted(specified.difference(used))
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `featuretools/primitives/base/aggregation_primitive_base.py`
- `featuretools/primitives/base/primitive_base.py`
- `featuretools/synthesis/deep_feature_synthesis.py`
- `featuretools/synthesis/utils.py`
