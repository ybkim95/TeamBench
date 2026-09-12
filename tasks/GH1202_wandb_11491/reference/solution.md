# Reference solution — GH1202_wandb_11491

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1202_wandb_11491`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1202_wandb_11491/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CHANGELOG.unreleased.md` (modified, +4/-0)
- `tests/unit_tests/test_lib/test_runid.py` (modified, +29/-9)
- `wandb/sdk/lib/runid.py` (modified, +8/-0)

## Diff Summary (What the Fix Changes)

### `wandb/sdk/lib/runid.py`
```diff
@@ -1,5 +1,6 @@
 """runid util."""
 
+import os
 import random
 import secrets
 from string import ascii_lowercase, digits
@@ -11,6 +12,13 @@
 _random = random.Random()
 
 
+# Reset the random number generator on forking a new process to avoid multiple processes using the same seed.
+# The `random` module basically does this internally for python's global random state.
+# This is only necessary on platforms that support the `fork` multiprocessing start method (e.g. POSIX).
+if hasattr(os, "fork"):
+    os.register_at_fork(after_in_child=_random.seed)
+
+
 def generate_id(length: int = 8) -> str:
     """Generate a random base-36 string of `length` digits."""
     # There are ~2.8T base-36 8-digit strings. If we generate 210k ids,
```

## Moved from `brief.md`

## Files That May Need Changes

- `wandb/sdk/lib/runid.py`
