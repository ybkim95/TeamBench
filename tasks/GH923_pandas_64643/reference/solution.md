# Reference solution — GH923_pandas_64643

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH923_pandas_64643`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH923_pandas_64643/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/source/whatsnew/v3.1.0.rst` (modified, +1/-0)
- `pandas/core/arrays/timedeltas.py` (modified, +9/-1)
- `pandas/core/tools/datetimes.py` (modified, +7/-15)
- `pandas/tests/tools/test_to_timedelta.py` (modified, +11/-0)

## Diff Summary (What the Fix Changes)

### `pandas/core/arrays/timedeltas.py`
```diff
@@ -1186,7 +1186,15 @@ def sequence_to_td64ns(
             #  back the requested unit (or closest-supported)
             with np.errstate(invalid="ignore"):
                 int_data = data.astype(np.int64)
-            all_round = (mask | (data == int_data)).all()
+            # On ARM, float-to-int64 overflow saturates to INT64_MAX
+            # instead of wrapping, which makes the data == int_data
+            # check pass incorrectly for OOB values like float(2**63).
+            # Exclude values outside the int64 domain from the check.
+            i64 = np.iinfo(np.int64)
+            in_int64_range = (data >= np.float64(i64.min)) & (
+                data < np.float64(i64.max)
+            )
+            all_round = (mask | (in_int64_range & (data == int_data))).all()
             if all_round:
                 result, _ = sequence_to_td64ns(
                     int_data, copy=False, unit=unit, errors=errors
```

### `pandas/core/tools/datetimes.py`
```diff
@@ -27,7 +27,6 @@
     Timestamp,
     astype_overflowsafe,
     get_supported_dtype,
-    iNaT,
     is_supported_dtype,
     timezones as libtimezones,
 )
@@ -515,22 +514,15 @@ def _to_datetime_with_unit(arg, unit, name, utc: bool, errors: str) -> Index:
 
         elif arg.dtype.kind == "f":
             mask = np.isnan(arg)
-            nat_as_float = np.float64(iNaT)
-            oob = (
-                (~mask)
-                & (arg != nat_as_float)
-                & ((arg >= np.float64(2**63)) | (arg < nat_as_float))
-            )
-            if oob.any():
-                if errors != "raise":
-                    return _to_datetime_with_unit(
-                        arg.astype(object), unit, name, utc, errors
-                    )
-                raise OutOfBoundsDatetime(f"cannot convert input with unit '{unit}'")
-
             with np.errstate(invalid="ignore"):
                 int_values = arg.astype(np.int64)
-            if (mask | (arg == int_values)).all():
+            # On ARM, float-to-int64 overflow saturates to INT64_MAX
+            # instead of wrapping, which makes the arg == int_values
+            # check pass incorrectly for OOB values like float(2**63).
+            # Exclude values outside the int64 domain from the check.
+            i64 = np.iinfo(np.int64)
+            in_int64_range = (arg >= np.float64(i64.min)) & (arg < np.float64(i64.max))
+            if (mask | (in_int64_range & (arg == int_values))).all():
                 # With all-round-or-NaN entries, we give the requested unit
                 #  back like with integers
                 result = _to_datetime_with_unit(
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `pandas/core/arrays/timedeltas.py`
- `pandas/core/tools/datetimes.py`
