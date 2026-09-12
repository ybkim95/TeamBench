# Reference solution — GH1124_featuretools_2434

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1124_featuretools_2434`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1124_featuretools_2434/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/source/release_notes.rst` (modified, +3/-0)
- `featuretools/primitives/standard/transform/binary/greater_than_equal_to_scalar.py` (modified, +2/-14)
- `featuretools/primitives/standard/transform/binary/greater_than_scalar.py` (modified, +2/-14)
- `featuretools/primitives/standard/transform/binary/less_than_equal_to_scalar.py` (modified, +2/-14)
- `featuretools/primitives/standard/transform/binary/less_than_scalar.py` (modified, +2/-14)
- `featuretools/tests/computational_backend/test_feature_set_calculator.py` (modified, +12/-12)
- `featuretools/tests/primitive_tests/test_transform_features.py` (modified, +0/-83)

## Diff Summary (What the Fix Changes)

### `featuretools/primitives/standard/transform/binary/greater_than_equal_to_scalar.py`
```diff
@@ -1,8 +1,5 @@
-import numpy as np
-import pandas as pd
-import pandas.api.types as pdtypes
 from woodwork.column_schema import ColumnSchema
-from woodwork.logical_types import BooleanNullable, Datetime, Ordinal
+from woodwork.logical_types import BooleanNullable
 
 from featuretools.primitives.base.transform_primitive_base import TransformPrimitive
 from featuretools.utils.gen_utils import Library
@@ -23,11 +20,7 @@ class GreaterThanEqualToScalar(TransformPrimitive):
     """
 
     name = "greater_than_equal_to_scalar"
-    input_types = [
-        [ColumnSchema(semantic_tags={"numeric"})],
-        [ColumnSchema(logical_type=Datetime)],
-        [ColumnSchema(logical_type=Ordinal)],
-    ]
+    input_types = [ColumnSchema(semantic_tags={"numeric"})]
     return_type = ColumnSchema(logical_type=BooleanNullable)
     compatibility = [Library.PANDAS, Library.DASK, Library.SPARK]
 
@@ -39,11 +32,6 @@ def __init__(self, value=0):
 
     def get_function(self):
         def greater_than_equal_to_scalar(vals):
-            if (
-                pdtypes.is_categorical_dtype(vals)
-                and self.value not in vals.cat.categories
-            ):
-                return vals.where(pd.isnull, np.nan)
             return vals >= self.value
 
         return greater_than_equal_to_scalar
```

### `featuretools/primitives/standard/transform/binary/greater_than_scalar.py`
```diff
@@ -1,8 +1,5 @@
-import numpy as np
-import pandas as pd
-import pandas.api.types as pdtypes
 from woodwork.column_schema import ColumnSchema
-from woodwork.logical_types import BooleanNullable, Datetime, Ordinal
+from woodwork.logical_types import BooleanNullable
 
 from featuretools.primitives.base.transform_primitive_base import TransformPrimitive
 from featuretools.utils.gen_utils import Library
@@ -23,11 +20,7 @@ class GreaterThanScalar(TransformPrimitive):
     """
 
     name = "greater_than_scalar"
-    input_types = [
-        [ColumnSchema(semantic_tags={"numeric"})],
-        [ColumnSchema(logical_type=Datetime)],
-        [ColumnSchema(logical_type=Ordinal)],
-    ]
+    input_types = [ColumnSchema(semantic_tags={"numeric"})]
     return_type = ColumnSchema(logical_type=BooleanNullable)
     compatibility = [Library.PANDAS, Library.DASK, Library.SPARK]
 
@@ -37,11 +30,6 @@ def __init__(self, value=0):
 
     def get_function(self):
         def greater_than_scalar(vals):
-            if (
-                pdtypes.is_categorical_dtype(vals)
-                and self.value not in vals.cat.categories
-            ):
-                return vals.where(pd.isnull, np.nan)
             return vals > self.value
 
         return greater_than_scalar
```

### `featuretools/primitives/standard/transform/binary/less_than_equal_to_scalar.py`
```diff
@@ -1,8 +1,5 @@
-import numpy as np
-import pandas as pd
-import pandas.api.types as pdtypes
 from woodwork.column_schema import ColumnSchema
-from woodwork.logical_types import BooleanNullable, Datetime, Ordinal
+from woodwork.logical_types import BooleanNullable
 
 from featuretools.primitives.base.transform_primitive_base import TransformPrimitive
 from featuretools.utils.gen_utils import Library
@@ -23,11 +20,7 @@ class LessThanEqualToScalar(TransformPrimitive):
     """
 
     name = "less_than_equal_to_scalar"
-    input_types = [
-        [ColumnSchema(semantic_tags={"numeric"})],
-        [ColumnSchema(logical_type=Datetime)],
-        [ColumnSchema(logical_type=Ordinal)],
-    ]
+    input_types = [ColumnSchema(semantic_tags={"numeric"})]
     return_type = ColumnSchema(logical_type=BooleanNullable)
     compatibility = [Library.PANDAS, Library.DASK, Library.SPARK]
 
@@ -39,11 +32,6 @@ def __init__(self, value=0):
 
     def get_function(self):
         def less_than_equal_to_scalar(vals):
-            if (
-                pdtypes.is_categorical_dtype(vals)
-                and self.value not in vals.cat.categories
-            ):
-                return vals.where(pd.isnull, np.nan)
             return vals <= self.value
 
         return less_than_equal_to_scalar
```

### `featuretools/primitives/standard/transform/binary/less_than_scalar.py`
```diff
@@ -1,8 +1,5 @@
-import numpy as np
-import pandas as pd
-import pandas.api.types as pdtypes
 from woodwork.column_schema import ColumnSchema
-from woodwork.logical_types import BooleanNullable, Datetime, Ordinal
+from woodwork.logical_types import BooleanNullable
 
 from featuretools.primitives.base.transform_primitive_base import TransformPrimitive
 from featuretools.utils.gen_utils import Library
@@ -23,11 +20,7 @@ class LessThanScalar(TransformPrimitive):
     """
 
     name = "less_than_scalar"
-    input_types = [
-        [ColumnSchema(semantic_tags={"numeric"})],
-        [ColumnSchema(logical_type=Datetime)],
-        [ColumnSchema(logical_type=Ordinal)],
-    ]
+    input_types = [ColumnSchema(semantic_tags={"numeric"})]
     return_type = ColumnSchema(logical_type=BooleanNullable)
     compatibility = [Library.PANDAS, Library.DASK, Library.SPARK]
 
@@ -37,11 +30,6 @@ def __init__(self, value=0):
 
     def get_function(self):
         def less_than_scalar(vals):
-            if (
-                pdtypes.is_categorical_dtype(vals)
-                and self.value not in vals.cat.categories
-            ):
-                return vals.where(pd.isnull, np.nan)
             return vals < self.value
 
         return less_than_scalar
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `featuretools/primitives/standard/transform/binary/greater_than_equal_to_scalar.py`
- `featuretools/primitives/standard/transform/binary/greater_than_scalar.py`
- `featuretools/primitives/standard/transform/binary/less_than_equal_to_scalar.py`
- `featuretools/primitives/standard/transform/binary/less_than_scalar.py`
