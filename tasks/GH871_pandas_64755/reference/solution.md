# Reference solution — GH871_pandas_64755

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH871_pandas_64755`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH871_pandas_64755/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `doc/source/whatsnew/v3.1.0.rst` (modified, +1/-0)
- `pandas/core/arrays/timedeltas.py` (modified, +11/-1)
- `pandas/core/tools/datetimes.py` (modified, +13/-0)
- `pandas/tests/tools/test_to_datetime.py` (modified, +36/-0)
- `pandas/tests/tools/test_to_timedelta.py` (modified, +36/-0)

## Diff Summary (What the Fix Changes)

### `pandas/core/arrays/timedeltas.py`
```diff
@@ -1169,7 +1169,13 @@ def sequence_to_td64ns(
 
     elif is_integer_dtype(data.dtype):
         # treat as multiples of the given unit
-        data, copy_made = _ints_to_td64ns(data, unit=unit)
+        try:
+            data, copy_made = _ints_to_td64ns(data, unit=unit)
+        except OutOfBoundsTimedelta:
+            if errors == "raise":
+                raise
+            data = _objects_to_td64ns(data.astype(object), unit=unit, errors=errors)
+            copy_made = True
         copy = copy and not copy_made
 
     elif is_float_dtype(data.dtype):
@@ -1254,6 +1260,10 @@ def _ints_to_td64ns(data, unit: str = "ns") -> tuple[np.ndarray, bool]:
     unit = unit if unit is not None else "ns"
 
     if data.dtype != np.int64:
+        # GH#60677 unsigned integers > int64 max overflow silently
+        # when cast to int64 (which timedelta64 is backed by)
+        if data.dtype == np.dtype("uint64") and (data > np.iinfo(np.int64).max).any():
+            raise OutOfBoundsTimedelta(f"Cannot convert input with unit '{unit}'")
         # converting to int64 makes a copy, so we can avoid
         # re-copying later
         data = data.astype(np.int64)
```

### `pandas/core/tools/datetimes.py`
```diff
@@ -501,6 +501,19 @@ def _to_datetime_with_unit(arg, unit, name, utc: bool, errors: str) -> Index:
         if arg.dtype.kind in "iu":
             # Note we can't do "f" here because that could induce unwanted
             #  rounding GH#14156, GH#20445
+
+            # GH#60677 unsigned integers > int64 max overflow silently
+            # when cast to datetime64 (which is backed by int64)
+            if arg.dtype == np.dtype("uint64"):
+                mask = arg > np.iinfo(np.int64).max
+                if mask.any():
+                    if errors == "raise":
+                        raise OutOfBoundsDatetime(
+                            f"cannot convert input with unit '{unit}'"
+                        )
+
+                    arg = arg.astype(object)
+                    return _to_datetime_with_unit(arg, unit, name, utc, errors)
             arr = arg.astype(f"datetime64[{unit}]", copy=False)
             dtype = get_supported_dtype(arr.dtype)
             try:
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `pandas/core/arrays/timedeltas.py`
- `pandas/core/tools/datetimes.py`
