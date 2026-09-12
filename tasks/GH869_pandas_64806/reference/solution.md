# Reference solution — GH869_pandas_64806

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH869_pandas_64806`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH869_pandas_64806/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/source/whatsnew/v3.1.0.rst` (modified, +1/-1)
- `pandas/_libs/tslibs/offsets.pyi` (modified, +4/-0)
- `pandas/core/arrays/datetimes.py` (modified, +17/-5)
- `pandas/tests/arithmetic/test_datetime64.py` (modified, +34/-0)

## Diff Summary (What the Fix Changes)

### `pandas/core/arrays/datetimes.py`
```diff
@@ -47,6 +47,7 @@
     tzconversion,
 )
 from pandas._libs.tslibs.dtypes import abbrev_to_npy_unit
+from pandas._libs.tslibs.offsets import RelativeDeltaOffset
 from pandas.errors import PerformanceWarning
 from pandas.util._decorators import set_module
 from pandas.util._exceptions import find_stack_level
@@ -839,6 +840,21 @@ def _assert_tzawareness_compat(self, other) -> None:
     def _add_offset(self, offset: BaseOffset) -> Self:
         assert not isinstance(offset, Tick)
 
+        # For pure-timedelta DateOffset with tz-aware data, add to UTC values
+        # directly to avoid nonexistent/ambiguous time errors from
+        # re-localizing wall-time results near DST (GH#28610).
+        if (
+            self.tz is not None
+            and isinstance(offset, RelativeDeltaOffset)
+            and not offset._use_relativedelta
+        ):
+            res_values = self._ndarray + offset._pd_timedelta
+            result = type(self)._simple_new(res_values, dtype=self.dtype)
+            if offset.normalize:
+                result = result.normalize()
+                result._freq = None
+            return result
+
         if self.tz is not None:
             values = self.tz_localize(None)
         else:
@@ -847,11 +863,7 @@ def _add_offset(self, offset: BaseOffset) -> Self:
         try:
             res_values = offset._apply_array(values._ndarray)
             if res_values.dtype.kind == "i":
-                # error: Argument 1 to "view" of "ndarray" has
-                # incompatible type
-                # "dtype[datetime64[date | int | None]] | DatetimeTZDtype";
-                # expected "dtype[Any] | _HasDType[dtype[Any]]"  [arg-type]
-                res_values = res_values.view(values.dtype)  # type: ignore[arg-type]
+                res_values = res_values.view(values.dtype)
         except NotImplementedError:
             if get_option("performance_warnings"):
                 warnings.warn(
```

## Moved from `brief.md`

## Files That May Need Changes

- `pandas/core/arrays/datetimes.py`
