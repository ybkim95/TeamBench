# Reference solution — GH894_great_expectati_4044

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH894_great_expectati_4044`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH894_great_expectati_4044/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `great_expectations/expectations/core/expect_column_values_to_be_in_type_list.py` (modified, +36/-3)
- `great_expectations/profile/base.py` (modified, +8/-0)
- `tests/expectations/core/test_expect_column_values_to_be_in_type_list.py` (modified, +48/-1)
- `tests/profile/test_jsonschema_profiler.py` (modified, +96/-0)

## Diff Summary (What the Fix Changes)

### `great_expectations/expectations/core/expect_column_values_to_be_in_type_list.py`
```diff
@@ -4,6 +4,7 @@
 
 import numpy as np
 import pandas as pd
+from packaging import version
 
 from great_expectations.core import ExpectationConfiguration
 from great_expectations.exceptions import InvalidExpectationConfigurationError
@@ -341,11 +342,18 @@ def _validate_pandas(
                 except TypeError:
                     try:
                         pd_type = getattr(pd, type_)
-                        if isinstance(pd_type, type):
-                            comp_types.append(pd_type)
                     except AttributeError:
                         pass
-
+                    else:
+                        if isinstance(pd_type, type):
+                            comp_types.append(pd_type)
+                            try:
+                                if isinstance(
+                                    pd_type(), pd.core.dtypes.base.ExtensionDtype
+                                ):
+                                    comp_types.append(pd_type())
+                            except TypeError:
+                                pass
                     try:
                         pd_type = getattr(pd.core.dtypes.dtypes, type_)
                         if isinstance(pd_type, type):
@@ -357,6 +365,31 @@ def _validate_pandas(
                 if native_type is not None:
                     comp_types.extend(native_type)
 
+            # TODO: Remove when Numpy >=1.21 is pinned as a dependency
+            _pandas_supports_extension_dtypes = version.parse(
+                pd.__version__
+            ) >= version.parse("0.24")
+            _numpy_doesnt_support_extensions_properly = version.parse(
+                np.__version__
+            ) < version.parse("1.21")
+            if (
+                _numpy_doesnt_support_extensions_properly
+                and _pandas_supports_extension_dtypes
+            ):
+                # This works around a bug where Pandas nullable int types aren't compatible with Numpy dtypes
+                # Note:
```

### `great_expectations/profile/base.py`
```diff
@@ -124,6 +124,14 @@ class ProfilerTypeMapping:
         "uint16",
         "uint32",
         "uint64",
+        "Int8Dtype",
+        "Int16Dtype",
+        "Int32Dtype",
+        "Int64Dtype",
+        "UInt8Dtype",
+        "UInt16Dtype",
+        "UInt32Dtype",
+        "UInt64Dtype",
         "INT",
         "INTEGER",
         "INT64",
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `great_expectations/expectations/core/expect_column_values_to_be_in_type_list.py`
- `great_expectations/profile/base.py`
