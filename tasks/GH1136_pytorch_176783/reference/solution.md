# Reference solution — GH1136_pytorch_176783

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1136_pytorch_176783`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1136_pytorch_176783/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `test/inductor/test_utils.py` (modified, +16/-0)
- `torch/utils/_sympy/functions.py` (modified, +32/-0)

## Diff Summary (What the Fix Changes)

### `torch/utils/_sympy/functions.py`
```diff
@@ -1366,6 +1366,38 @@ def __int__(self) -> int:
         # pyrefly: ignore [missing-attribute]
         return int(self.args[0])
 
+    def _identity_atom_compare(self, other, op):
+        """
+        Fast path for comparing wrapped numeric atomics against other numeric atomics.
+        Keep compound expressions on SymPy's default symbolic path.
+        """
+        arg = self.args[0]
+        if isinstance(other, int):
+            other = sympy.Integer(other)
+        if not isinstance(other, sympy.Expr):
+            return None
+        if not (arg.is_Atom and arg.is_number and arg.is_comparable):
+            return None
+        if not (other.is_Atom and other.is_number and other.is_comparable):
+            return None
+        return sympy.S.true if op(arg, other) else sympy.S.false
+
+    def __ge__(self, other):
+        out = self._identity_atom_compare(other, lambda a, b: a >= b)
+        return out if out is not None else super().__ge__(other)
+
+    def __gt__(self, other):
+        out = self._identity_atom_compare(other, lambda a, b: a > b)
+        return out if out is not None else super().__gt__(other)
+
+    def __le__(self, other):
+        out = self._identity_atom_compare(other, lambda a, b: a <= b)
+        return out if out is not None else super().__le__(other)
+
+    def __lt__(self, other):
+        out = self._identity_atom_compare(other, lambda a, b: a < b)
+        return out if out is not None else super().__lt__(other)
+
     def __float__(self) -> float:
         # pyrefly: ignore [missing-attribute]
         return float(self.args[0])
```

## Moved from `brief.md`

## Files That May Need Changes

- `torch/utils/_sympy/functions.py`
