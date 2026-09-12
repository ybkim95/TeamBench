# Reference solution — GH1061_featuretools_2627

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1061_featuretools_2627`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1061_featuretools_2627/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `.github/workflows/tests_with_latest_deps.yaml` (modified, +1/-1)
- `docs/source/release_notes.rst` (modified, +1/-0)
- `featuretools/primitives/standard/aggregation/percent_true.py` (modified, +2/-1)
- `featuretools/tests/primitive_tests/aggregation_primitive_tests/test_percent_true.py` (added, +40/-0)

## Diff Summary (What the Fix Changes)

### `featuretools/primitives/standard/aggregation/percent_true.py`
```diff
@@ -1,3 +1,4 @@
+import pandas as pd
 from woodwork.column_schema import ColumnSchema
 from woodwork.logical_types import Boolean, BooleanNullable, Double
 
@@ -30,7 +31,7 @@ class PercentTrue(AggregationPrimitive):
     return_type = ColumnSchema(logical_type=Double, semantic_tags={"numeric"})
     stack_on = []
     stack_on_exclude = []
-    default_value = 0
+    default_value = pd.NA
     compatibility = [Library.PANDAS, Library.DASK]
     description_template = "the percentage of true values in {}"
 
```

## Moved from `brief.md`

## Files That May Need Changes

- `featuretools/primitives/standard/aggregation/percent_true.py`
