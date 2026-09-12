# Reference solution — GH997_pytorch_lightni_21395

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH997_pytorch_lightni_21395`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH997_pytorch_lightni_21395/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `src/lightning/pytorch/CHANGELOG.md` (modified, +3/-0)
- `src/lightning/pytorch/profilers/profiler.py` (modified, +9/-2)
- `tests/tests_pytorch/profilers/test_profiler.py` (modified, +27/-0)

## Diff Summary (What the Fix Changes)

### `src/lightning/pytorch/profilers/profiler.py`
```diff
@@ -15,6 +15,7 @@
 
 import logging
 import os
+import re
 from abc import ABC, abstractmethod
 from collections.abc import Generator
 from contextlib import contextmanager
@@ -80,7 +81,6 @@ def _prepare_filename(
         self,
         action_name: Optional[str] = None,
         extension: str = ".txt",
-        split_token: str = "-",  # noqa: S107
     ) -> str:
         args = []
         if self._stage is not None:
@@ -91,7 +91,14 @@ def _prepare_filename(
             args.append(str(self._local_rank))
         if action_name is not None:
             args.append(action_name)
-        return split_token.join(args) + extension
+        base = "-".join(args)
+        # Replace a set of path-unsafe characters across platforms with '_'
+        base = re.sub(r"[\\/:*?\"<>|\n\r\t]", "_", base)
+        base = re.sub(r"_+", "_", base)
+        base = base.strip()
+        if not base:
+            base = "profile"
+        return base + extension
 
     def _prepare_streams(self) -> None:
         if self._write_stream is not None:
```

## Moved from `brief.md`

## Files That May Need Changes

- `src/lightning/pytorch/profilers/profiler.py`
