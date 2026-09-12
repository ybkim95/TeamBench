# Reference solution — GH868_pandas_64809

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH868_pandas_64809`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH868_pandas_64809/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/source/whatsnew/v3.1.0.rst` (modified, +1/-0)
- `pandas/_libs/tslibs/offsets.pyx` (modified, +2/-1)
- `pandas/core/arrays/datetimes.py` (modified, +11/-5)
- `pandas/tests/tseries/offsets/test_offsets.py` (modified, +22/-0)

## Diff Summary (What the Fix Changes)

### `pandas/core/arrays/datetimes.py`
```diff
@@ -30,6 +30,7 @@
     OutOfBoundsDatetime,
     OutOfBoundsTimedelta,
     Resolution,
+    Timedelta,
     Timestamp,
     astype_overflowsafe,
     fields,
@@ -98,10 +99,7 @@
         npt,
     )
 
-    from pandas import (
-        DataFrame,
-        Timedelta,
-    )
+    from pandas import DataFrame
     from pandas.core.arrays import PeriodArray
 
     _TimestampNoneT1 = TypeVar("_TimestampNoneT1", Timestamp, None)
@@ -861,7 +859,15 @@ def _add_offset(self, offset: BaseOffset) -> Self:
                     stacklevel=find_stack_level(),
                 )
             res_values = self.astype("O") + offset
-            result = type(self)._from_sequence(res_values, dtype=self.dtype)
+            # GH#56586 use the finer resolution between self and offset.offset
+            # to avoid truncating sub-unit precision
+            res_unit = self.unit
+            if hasattr(offset, "offset") and offset.offset:
+                offset_unit = Timedelta(offset.offset).unit
+                if abbrev_to_npy_unit(offset_unit) > abbrev_to_npy_unit(res_unit):
+                    res_unit = offset_unit
+            dtype = tz_to_dtype(self.tz, unit=res_unit)
+            result = type(self)._from_sequence(res_values, dtype=dtype)
 
         else:
             result = type(self)._simple_new(res_values, dtype=res_values.dtype)
```

## Moved from `brief.md`

## Files That May Need Changes

- `pandas/core/arrays/datetimes.py`
