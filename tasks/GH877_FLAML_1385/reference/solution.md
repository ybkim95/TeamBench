# Reference solution — GH877_FLAML_1385

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH877_FLAML_1385`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH877_FLAML_1385/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `flaml/automl/automl.py` (modified, +3/-3)
- `flaml/automl/task/generic_task.py` (modified, +2/-2)
- `flaml/automl/task/task.py` (modified, +1/-1)
- `test/automl/test_split.py` (modified, +33/-3)

## Diff Summary (What the Fix Changes)

### `flaml/automl/automl.py`
```diff
@@ -203,7 +203,7 @@ def custom_metric(
                 * Valid str options depend on different tasks.
                 For classification tasks, valid choices are
                     ["auto", 'stratified', 'uniform', 'time', 'group']. "auto" -> stratified.
-                For regression tasks, valid choices are ["auto", 'uniform', 'time'].
+                For regression tasks, valid choices are ["auto", 'uniform', 'time', 'group'].
                     "auto" -> uniform.
                 For time series forecast tasks, must be "auto" or 'time'.
                 For ranking task, must be "auto" or 'group'.
@@ -739,7 +739,7 @@ def retrain_from_log(
                 * Valid str options depend on different tasks.
                 For classification tasks, valid choices are
                     ["auto", 'stratified', 'uniform', 'time', 'group']. "auto" -> stratified.
-                For regression tasks, valid choices are ["auto", 'uniform', 'time'].
+                For regression tasks, valid choices are ["auto", 'uniform', 'time', 'group'].
                     "auto" -> uniform.
                 For time series forecast tasks, must be "auto" or 'time'.
                 For ranking task, must be "auto" or 'group'.
@@ -1358,7 +1358,7 @@ def custom_metric(
                 * Valid str options depend on different tasks.
                 For classification tasks, valid choices are
                     ["auto", 'stratified', 'uniform', 'time', 'group']. "auto" -> stratified.
-                For regression tasks, valid choices are ["auto", 'uniform', 'time'].
+                For regression tasks, valid choices are ["auto", 'uniform', 'time', 'group'].
                     "auto" -> uniform.
                 For time series forecast tasks, must be "auto" or 'time'.
                 For ranking task, must be "auto" or 'group'.
```

### `flaml/automl/task/generic_task.py`
```diff
@@ -442,8 +442,8 @@ def prepare_data(
                 X_train_all, y_train_all = shuffle(X_train_all, y_train_all, random_state=RANDOM_SEED)
             if data_is_df:
                 X_train_all.reset_index(drop=True, inplace=True)
-            if isinstance(y_train_all, pd.Series):
-                y_train_all.reset_index(drop=True, inplace=True)
+        if isinstance(y_train_all, pd.Series):
+            y_train_all.reset_index(drop=True, inplace=True)
 
         X_train, y_train = X_train_all, y_train_all
         state.groups_all = state.groups
```

### `flaml/automl/task/task.py`
```diff
@@ -192,7 +192,7 @@ def prepare_data(
                 * Valid str options depend on different tasks.
                 For classification tasks, valid choices are
                     ["auto", 'stratified', 'uniform', 'time', 'group']. "auto" -> stratified.
-                For regression tasks, valid choices are ["auto", 'uniform', 'time'].
+                For regression tasks, valid choices are ["auto", 'uniform', 'time', 'group'].
                     "auto" -> uniform.
                 For time series forecast tasks, must be "auto" or 'time'.
                 For ranking task, must be "auto" or 'group'.
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `flaml/automl/automl.py`
- `flaml/automl/task/generic_task.py`
- `flaml/automl/task/task.py`
