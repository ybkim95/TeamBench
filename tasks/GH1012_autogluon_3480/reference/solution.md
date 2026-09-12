# Reference solution — GH1012_autogluon_3480

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1012_autogluon_3480`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1012_autogluon_3480/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `core/src/autogluon/core/utils/utils.py` (modified, +18/-3)
- `core/tests/unittests/utils/test_utils.py` (modified, +56/-0)

## Diff Summary (What the Fix Changes)

### `core/src/autogluon/core/utils/utils.py`
```diff
@@ -472,9 +472,24 @@ def generate_train_test_split(
                 y_split = y.drop(index=rare_indices)
                 stratify = y_split
 
-    X_train, X_test, y_train, y_test = train_test_split(
-        X_split, y_split.values, test_size=test_size, shuffle=True, random_state=random_state, stratify=stratify
-    )
+    try:
+        X_train, X_test, y_train, y_test = train_test_split(
+            X_split, y_split.values, test_size=test_size, shuffle=True, random_state=random_state, stratify=stratify
+        )
+    except ValueError:
+        # This logic is necessary to avoid an edge-case limitation of scikit-learn's train_test_split function that leads to the following error:
+        #  ValueError: The test_size = FOO should be greater or equal to the number of classes = BAR
+        # When the number of classes is greater than the resulting number of test rows, and stratification is enabled, it will raise an exception.
+        #  Logically the code should still work, but for some reason scikit-learn doesn't allow this scenario.
+        #  To handle it without erroring, we disable stratification in this case. This isn't ideal, but proper solutions involve patching scikit-learn.
+        if stratify is None:
+            raise
+        X_train, X_test, y_train, y_test = train_test_split(
+            X_split, y_split.values, test_size=test_size, shuffle=True, random_state=random_state, stratify=None
+        )
+        if len(y_test) >= len(y_split.unique()):
+            # This should never occur, otherwise the original exception is not an expected one
+            raise
     if problem_type != SOFTCLASS:
         y_train = pd.Series(y_train, index=X_train.index)
         y_test = pd.Series(y_test, index=X_test.index)
```

## Moved from `brief.md`

## Files That May Need Changes

- `core/src/autogluon/core/utils/utils.py`
