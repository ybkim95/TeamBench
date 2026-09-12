# Reference solution — GH875_great_expectati_1616

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH875_great_expectati_1616`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH875_great_expectati_1616/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/reference/changelog.rst` (modified, +3/-2)
- `great_expectations/profile/basic_suite_builder_profiler.py` (modified, +4/-3)
- `tests/profile/fixtures/expected_evrs_BasicSuiteBuilderProfiler_on_titanic_demo_mode.json` (modified, +1/-1)
- `tests/profile/fixtures/expected_evrs_SuiteBuilderProfiler_on_titanic_with_configurations.json` (modified, +1/-1)
- `tests/profile/test_basic_suite_builder_profiler.py` (modified, +4/-4)

## Diff Summary (What the Fix Changes)

### `great_expectations/profile/basic_suite_builder_profiler.py`
```diff
@@ -153,10 +153,11 @@ def _create_non_nullity_expectations(cls, dataset, column):
         not_null_result = dataset.expect_column_values_to_not_be_null(column)
         if not not_null_result.success:
             unexpected_percent = float(not_null_result.result["unexpected_percent"])
-            mostly_value = round(
-                max(0.001, (100.0 - unexpected_percent - 10) / 100.0), 2
+            potential_mostly_value = (100.0 - unexpected_percent - 10) / 100.0
+            safe_mostly_value = round(max(0.001, potential_mostly_value), 3)
+            dataset.expect_column_values_to_not_be_null(
+                column, mostly=safe_mostly_value
             )
-            dataset.expect_column_values_to_not_be_null(column, mostly=mostly_value)
 
     @classmethod
     def _create_expectations_for_numeric_column(cls, dataset, column):
```

## Moved from `brief.md`

## Files That May Need Changes

- `great_expectations/profile/basic_suite_builder_profiler.py`
