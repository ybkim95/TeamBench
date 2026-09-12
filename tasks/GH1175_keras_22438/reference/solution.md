# Reference solution — GH1175_keras_22438

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1175_keras_22438`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1175_keras_22438/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `keras/src/regularizers/regularizers.py` (modified, +11/-7)
- `keras/src/regularizers/regularizers_test.py` (modified, +4/-3)

## Diff Summary (What the Fix Changes)

### `keras/src/regularizers/regularizers.py`
```diff
@@ -195,15 +195,19 @@ def __init__(self, l1=0.0, l2=0.0):
         validate_float_arg(l1, name="l1")
         validate_float_arg(l2, name="l2")
 
-        self.l1 = l1
-        self.l2 = l2
+        self.l1 = ops.convert_to_tensor(l1)
+        self.l2 = ops.convert_to_tensor(l2)
 
     def __call__(self, x):
         regularization = ops.convert_to_tensor(0.0, dtype=x.dtype)
         if self.l1:
-            regularization += self.l1 * ops.sum(ops.absolute(x))
+            regularization += ops.cast(self.l1, dtype=x.dtype) * ops.sum(
+                ops.absolute(x)
+            )
         if self.l2:
-            regularization += self.l2 * ops.sum(ops.square(x))
+            regularization += ops.cast(self.l2, dtype=x.dtype) * ops.sum(
+                ops.square(x)
+            )
         return regularization
 
     def get_config(self):
@@ -233,7 +237,7 @@ def __init__(self, l1=0.01):
         self.l1 = ops.convert_to_tensor(l1)
 
     def __call__(self, x):
-        return self.l1 * ops.sum(ops.absolute(x))
+        return ops.cast(self.l1, dtype=x.dtype) * ops.sum(ops.absolute(x))
 
     def get_config(self):
         return {"l1": float(self.l1)}
@@ -259,10 +263,10 @@ class L2(Regularizer):
     def __init__(self, l2=0.01):
         l2 = 0.01 if l2 is None else l2
         validate_float_arg(l2, name="l2")
-        self.l2 = l2
+        self.l2 = ops.convert_to_tensor(l2)
 
     def __call__(self, x):
-        return self.l2 * ops.sum(ops.square(x))
+        return ops.cast(self.l2, dtype=x.dtype) * ops.sum(ops.square(x))
 
     def get_config(self):
         return {"l2": float(self.l2)}
```

## Moved from `brief.md`

## Files That May Need Changes

- `keras/src/regularizers/regularizers.py`
