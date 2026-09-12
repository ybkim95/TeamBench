# Reference solution — GH944_autogluon_2986

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH944_autogluon_2986`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH944_autogluon_2986/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `features/src/autogluon/features/generators/abstract.py` (modified, +2/-1)
- `features/src/autogluon/features/generators/astype.py` (modified, +7/-2)
- `features/tests/features/conftest.py` (modified, +38/-2)
- `features/tests/features/generators/test_auto_ml_pipeline.py` (modified, +152/-0)
- `features/tests/features/generators/test_bulk.py` (modified, +1/-1)

## Diff Summary (What the Fix Changes)

### `features/src/autogluon/features/generators/abstract.py`
```diff
@@ -518,7 +518,8 @@ def _remove_features_in(self, features: list):
                 self._feature_metadata_before_post = self._feature_metadata_before_post.keep_features(features_to_keep)
 
             self.feature_metadata_in = self.feature_metadata_in.remove_features(features=features)
-            self.features_in = self.feature_metadata_in.get_features()
+            features_in_new = set(self.feature_metadata_in.get_features())
+            self.features_in = [f for f in self.features_in if f in features_in_new]
             if self._pre_astype_generator:
                 self._pre_astype_generator._remove_features_out(features)
 
```

### `features/src/autogluon/features/generators/astype.py`
```diff
@@ -181,15 +181,20 @@ def _convert_to_bool_fast_batch(self, X: DataFrame) -> DataFrame:
         for feature in self._bool_features_list:
             X_bool_list.append((X[feature] == self._bool_features[feature]).astype(np.int8))
         X_bool = pd.concat(X_bool_list, axis=1)
-        return pd.concat([X[self._non_bool_features_list], X_bool], axis=1)
+
+        # TODO: re-order columns to features_in required because `feature_interactions=False` to avoid error when feature prune.
+        #  Note that this is slower than avoiding the re-order, but avoiding the re-order is very complicated to do correctly.
+        return pd.concat([X[self._non_bool_features_list], X_bool], axis=1)[self.features_in]
 
     def _convert_to_bool_fast_realtime(self, X: DataFrame) -> DataFrame:
         """Optimized for when X is <= 100 rows"""
         X_bool_features_np = X[self._bool_features_list].to_numpy(dtype='object')
         X_bool_numpy = X_bool_features_np == self._bool_features_val_np
         X_bool = pd.DataFrame(X_bool_numpy, columns=self._bool_features_list, dtype=np.int8, index=X.index)
 
-        return pd.concat([X[self._non_bool_features_list], X_bool], axis=1)
+        # TODO: re-order columns to features_in required because `feature_interactions=False` to avoid error when feature prune.
+        #  Note that this is slower than avoiding the re-order, but avoiding the re-order is very complicated to do correctly.
+        return pd.concat([X[self._non_bool_features_list], X_bool], axis=1)[self.features_in]
 
     @staticmethod
     def get_default_infer_features_in_args() -> dict:
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `features/src/autogluon/features/generators/abstract.py`
- `features/src/autogluon/features/generators/astype.py`
