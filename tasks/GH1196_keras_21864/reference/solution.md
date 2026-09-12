# Reference solution — GH1196_keras_21864

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1196_keras_21864`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1196_keras_21864/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `keras/src/backend/common/variables.py` (modified, +1/-1)
- `keras/src/backend/common/variables_test.py` (modified, +30/-2)

## Diff Summary (What the Fix Changes)

### `keras/src/backend/common/variables.py`
```diff
@@ -276,7 +276,7 @@ def value(self):
         return self._maybe_autocast(self._value)
 
     def assign(self, value):
-        value = self._convert_to_tensor(value, dtype=self.dtype)
+        value = self._convert_to_tensor(value, dtype=self._dtype)
         if not shape_equal(value.shape, self.shape):
             raise ValueError(
                 "The shape of the target variable and "
```

## Moved from `brief.md`

## Files That May Need Changes

- `keras/src/backend/common/variables.py`
