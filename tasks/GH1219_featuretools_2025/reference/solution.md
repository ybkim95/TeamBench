# Reference solution — GH1219_featuretools_2025

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1219_featuretools_2025`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1219_featuretools_2025/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/source/release_notes.rst` (modified, +1/-1)
- `featuretools/primitives/standard/binary_transform.py` (modified, +52/-4)
- `featuretools/tests/primitive_tests/test_transform_features.py` (modified, +77/-2)

## Diff Summary (What the Fix Changes)

### `featuretools/primitives/standard/binary_transform.py`
```diff
@@ -36,7 +36,19 @@ class GreaterThan(TransformPrimitive):
     description_template = "whether {} is greater than {}"
 
     def get_function(self):
-        return np.greater
+        def greater_than(val1, val2):
+            val1_is_categorical = pdtypes.is_categorical_dtype(val1)
+            val2_is_categorical = pdtypes.is_categorical_dtype(val2)
+            if val1_is_categorical and val2_is_categorical:
+                if not all(val1.cat.categories == val2.cat.categories):
+                    return np.nan
+            elif val1_is_categorical or val2_is_categorical:
+                # This can happen because CFM does not set proper dtypes for intermediate
+                # features, so some agg features that should be Ordinal don't yet have correct type.
+                return np.nan
+            return val1 > val2
+
+        return greater_than
 
     def generate_name(self, base_feature_names):
         return "%s > %s" % (base_feature_names[0], base_feature_names[1])
@@ -112,7 +124,19 @@ class GreaterThanEqualTo(TransformPrimitive):
     description_template = "whether {} is greater than or equal to {}"
 
     def get_function(self):
-        return np.greater_equal
+        def greater_than_equal(val1, val2):
+            val1_is_categorical = pdtypes.is_categorical_dtype(val1)
+            val2_is_categorical = pdtypes.is_categorical_dtype(val2)
+            if val1_is_categorical and val2_is_categorical:
+                if not all(val1.cat.categories == val2.cat.categories):
+                    return np.nan
+            elif val1_is_categorical or val2_is_categorical:
+                # This can happen because CFM does not set proper dtypes for intermediate
+                # features, so some agg features that should be Ordinal don't yet have correct type.
+                return np.nan
+            return val1 >= val2
+
+        return greater_than_equal
 
     def generate_name(self, base_feature_names):
         return "%s >= %s" % (base_
```

## Moved from `brief.md`

## Files That May Need Changes

- `featuretools/primitives/standard/binary_transform.py`
