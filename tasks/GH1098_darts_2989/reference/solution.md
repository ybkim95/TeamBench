# Reference solution — GH1098_darts_2989

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1098_darts_2989`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1098_darts_2989/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CHANGELOG.md` (modified, +1/-0)
- `darts/dataprocessing/transformers/static_covariates_transformer.py` (modified, +28/-31)
- `darts/tests/dataprocessing/transformers/test_static_covariates_transformer.py` (modified, +43/-0)

## Diff Summary (What the Fix Changes)

### `darts/dataprocessing/transformers/static_covariates_transformer.py`
```diff
@@ -175,11 +175,13 @@ def ts_fit(
         # Collate static covariates of all `series`:
         stat_covs = pd.concat([s.static_covariates for s in series], axis=0)
 
-        cols_num, cols_cat = StaticCovariatesTransformer._infer_static_cov_dtypes(
-            stat_covs, cols_num, cols_cat
-        )
-
-        mask_num, mask_cat = StaticCovariatesTransformer._create_component_masks(
+        # Extract column names and masks in data order
+        (
+            cols_num,
+            cols_cat,
+            mask_num,
+            mask_cat,
+        ) = StaticCovariatesTransformer._process_static_cov_columns(
             stat_covs, cols_num, cols_cat
         )
 
@@ -227,45 +229,40 @@ def ts_fit(
         }
 
     @staticmethod
-    def _infer_static_cov_dtypes(
+    def _process_static_cov_columns(
         stat_covs: pd.DataFrame,
         cols_num: Optional[Sequence[str]],
         cols_cat: Optional[Sequence[str]],
-    ):
+    ) -> tuple[list[str], list[str], np.ndarray, np.ndarray]:
         """
-        Returns a list of names of numerical static covariates and a list
-        of names of categorical/ordinal static covariates.
+        Extracts numerical and categorical static covariate (component / columns) names and their component masks
+        in order of the input data.
+
+        Returns
+        -------
+        tuple
+            A tuple containing:
+            - cols_num: list of numerical column names in data order
+            - cols_cat: list of categorical column names in data order
+            - mask_num: boolean array indicating numerical columns
+            - mask_cat: boolean array indicating categorical columns
         """
         if cols_num is None:
             mask_num = stat_covs.columns.isin(
                 stat_covs.select_dtypes(include=np.number).columns
             )
-            cols_num = stat_covs.columns[mask_num]
+        else:
+            mask_num = stat_covs.columns.isin(cols_num)
+        cols_num = stat_covs.
```

## Moved from `brief.md`

## Files That May Need Changes

- `darts/dataprocessing/transformers/static_covariates_transformer.py`
