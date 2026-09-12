# Reference solution — GH1081_FLAML_1406

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1081_FLAML_1406`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1081_FLAML_1406/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `.github/workflows/python-package.yml` (modified, +1/-1)
- `flaml/automl/model.py` (modified, +10/-5)
- `test/automl/test_model.py` (renamed, +1/-0)

## Diff Summary (What the Fix Changes)

### `flaml/automl/model.py`
```diff
@@ -9,6 +9,7 @@
 import shutil
 import signal
 import sys
+import threading
 import time
 import warnings
 from contextlib import contextmanager
@@ -89,21 +90,25 @@ def limit_resource(memory_limit, time_limit):
             except ValueError:
                 # According to https://bugs.python.org/issue40518, it's a mac-specific error.
                 pass
-    main_thread = False
-    if time_limit is not None:
+    alarm_set = False
+    if time_limit is not None and threading.current_thread() is threading.main_thread():
         try:
             signal.signal(signal.SIGALRM, TimeoutHandler)
             signal.alarm(int(time_limit) or 1)
-            main_thread = True
+            alarm_set = True
         except ValueError:
             pass
+
     try:
         yield
     finally:
-        if main_thread:
+        if alarm_set:
             signal.alarm(0)
         if memory_limit > 0:
-            resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
+            try:
+                resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
+            except ValueError:
+                pass
 
 
 class BaseEstimator:
```

## Moved from `brief.md`

## Files That May Need Changes

- `flaml/automl/model.py`
