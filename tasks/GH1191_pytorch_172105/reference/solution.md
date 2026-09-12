# Reference solution — GH1191_pytorch_172105

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1191_pytorch_172105`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1191_pytorch_172105/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `test/test_serialization.py` (modified, +147/-0)
- `torch/_weights_only_unpickler.py` (modified, +10/-1)
- `torch/csrc/jit/python/init.cpp` (modified, +14/-1)

## Diff Summary (What the Fix Changes)

### `torch/_weights_only_unpickler.py`
```diff
@@ -466,9 +466,11 @@ def load(self):
                 list_obj.extend(items)
             elif key[0] == SETITEM[0]:
                 (v, k) = (self.stack.pop(), self.stack.pop())
+                self._check_set_item_target("SETITEM")
                 self.stack[-1][k] = v
             elif key[0] == SETITEMS[0]:
                 items = self.pop_mark()
+                self._check_set_item_target("SETITEMS")
                 for i in range(0, len(items), 2):
                     self.stack[-1][items[i]] = items[i + 1]
             elif key[0] == MARK[0]:
@@ -532,7 +534,7 @@ def load(self):
                     and torch.serialization._maybe_decode_ascii(pid[0]) != "storage"
                 ):
                     raise UnpicklingError(
-                        f"Only persistent_load of storage is allowed, but got {pid[0]}"
+                        f"Only persistent_load of storage is allowed, but got {type(pid[0])}"
                     )
                 self.append(self.persistent_load(pid))
             elif key[0] in [BINGET[0], LONG_BINGET[0]]:
@@ -571,6 +573,13 @@ def pop_mark(self):
         self.append = self.stack.append
         return items
 
+    def _check_set_item_target(self, opcode: str):
+        if type(self.stack[-1]) not in [dict, OrderedDict, Counter]:
+            raise UnpicklingError(
+                f"Can only {opcode} for dict, collections.OrderedDict, "
+                f"collections.Counter, but got {type(self.stack[-1])}"
+            )
+
     def persistent_load(self, pid):
         raise UnpicklingError("unsupported persistent id encountered")
 
```

## Moved from `brief.md`

## Files That May Need Changes

- `torch/_weights_only_unpickler.py`
