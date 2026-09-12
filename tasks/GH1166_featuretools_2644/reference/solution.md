# Reference solution — GH1166_featuretools_2644

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1166_featuretools_2644`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1166_featuretools_2644/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `.github/workflows/tests_with_latest_deps.yaml` (modified, +1/-1)
- `docs/source/release_notes.rst` (modified, +2/-1)
- `featuretools/primitives/standard/transform/cumulative/cumulative_time_since_last_false.py` (modified, +1/-1)
- `featuretools/primitives/standard/transform/cumulative/cumulative_time_since_last_true.py` (modified, +1/-1)
- `featuretools/primitives/standard/transform/datetime/date_to_holiday.py` (modified, +2/-2)
- `featuretools/tests/entityset_tests/test_serialization.py` (modified, +2/-2)
- `featuretools/tests/primitive_tests/test_feature_serialization.py` (modified, +2/-2)
- `featuretools/tests/primitive_tests/transform_primitive_tests/test_datetoholiday_primitive.py` (modified, +2/-2)
- `featuretools/tests/requirement_files/minimum_test_requirements.txt` (modified, +2/-2)
- `pyproject.toml` (modified, +7/-8)

## Diff Summary (What the Fix Changes)

### `featuretools/primitives/standard/transform/cumulative/cumulative_time_since_last_false.py`
```diff
@@ -51,7 +51,7 @@ def time_since_previous_false(datetime_col, bool_col):
             df.loc[not_false_indices, "last_false_datetime"] = np.nan
             df["last_false_datetime"] = df["last_false_datetime"].fillna(method="ffill")
             total_seconds = (
-                df["datetime"] - df["last_false_datetime"]
+                pd.to_datetime(df["datetime"]).subtract(df["last_false_datetime"])
             ).dt.total_seconds()
             return pd.Series(total_seconds)
 
```

### `featuretools/primitives/standard/transform/cumulative/cumulative_time_since_last_true.py`
```diff
@@ -46,7 +46,7 @@ def time_since_previous_true(datetime_col, bool_col):
             df.loc[~not_false_indices, "last_true_datetime"] = np.nan
             df["last_true_datetime"] = df["last_true_datetime"].fillna(method="ffill")
             total_seconds = (
-                df["datetime"] - df["last_true_datetime"]
+                pd.to_datetime(df["datetime"]).subtract(df["last_true_datetime"])
             ).dt.total_seconds()
             return pd.Series(total_seconds)
 
```

### `featuretools/primitives/standard/transform/datetime/date_to_holiday.py`
```diff
@@ -33,9 +33,9 @@ class DateToHoliday(TransformPrimitive):
         >>> date_to_holiday_canada = DateToHoliday(country='Canada')
         >>> dates = pd.Series([datetime(2016, 7, 1),
         ...          datetime(2016, 11, 15),
-        ...          datetime(2018, 9, 3)])
+        ...          datetime(2018, 12, 25)])
         >>> date_to_holiday_canada(dates).tolist()
-        ['Canada Day', nan, 'Labour Day']
+        ['Canada Day', nan, 'Christmas Day']
     """
 
     name = "date_to_holiday"
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `featuretools/primitives/standard/transform/cumulative/cumulative_time_since_last_false.py`
- `featuretools/primitives/standard/transform/cumulative/cumulative_time_since_last_true.py`
- `featuretools/primitives/standard/transform/datetime/date_to_holiday.py`
