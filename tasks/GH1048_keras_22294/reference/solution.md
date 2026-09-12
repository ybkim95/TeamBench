# Reference solution — GH1048_keras_22294

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1048_keras_22294`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1048_keras_22294/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `keras/src/utils/progbar.py` (modified, +3/-3)
- `keras/src/utils/progbar_test.py` (modified, +10/-0)

## Diff Summary (What the Fix Changes)

### `keras/src/utils/progbar.py`
```diff
@@ -119,7 +119,7 @@ def update(self, current, values=None, finalize=None):
             else:
                 message += "\n"
 
-            if self.target is not None:
+            if self.target is not None and self.target > 0:
                 numdigits = int(math.log10(self.target)) + 1
                 bar = (f"%{numdigits}d/%d") % (current, self.target)
                 bar = f"\x1b[1m{bar}\x1b[0m "
@@ -138,7 +138,7 @@ def update(self, current, values=None, finalize=None):
             message += bar
 
             # Add ETA if applicable
-            if self.target is not None and not finalize:
+            if self.target is not None and self.target > 0 and not finalize:
                 eta = time_per_unit * (self.target - current)
                 if eta > 3600:
                     eta_format = "%d:%02d:%02d" % (
@@ -186,7 +186,7 @@ def update(self, current, values=None, finalize=None):
             message = ""
 
         elif self.verbose == 2:
-            if finalize:
+            if finalize and self.target is not None and self.target > 0:
                 numdigits = int(math.log10(self.target)) + 1
                 count = f"%{numdigits}d/%d" % (current, self.target)
                 info = f"{count} - {now - self._start:.0f}s"
```

## Moved from `brief.md`

## Files That May Need Changes

- `keras/src/utils/progbar.py`
