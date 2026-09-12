# Reference solution — GH1090_statsmodels_9457

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1090_statsmodels_9457`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1090_statsmodels_9457/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `statsmodels/tsa/tests/test_x13.py` (modified, +42/-13)
- `statsmodels/tsa/x13.py` (modified, +186/-112)

## Diff Summary (What the Fix Changes)

### `statsmodels/tsa/x13.py`
```diff
@@ -7,42 +7,45 @@
 Many of the functions are called x12. However, they are also intended to work
 for x13. If this is not the case, it's a bug.
 """
+
 from statsmodels.compat.pandas import deprecate_kwarg
 
 import os
+import re
 import subprocess
 import tempfile
-import re
 from warnings import warn
 
 import pandas as pd
 
+from statsmodels.tools.sm_exceptions import (
+    IOWarning,
+    X13Error,
+    X13NotFoundError,
+    X13Warning,
+)
 from statsmodels.tools.tools import Bunch
-from statsmodels.tools.sm_exceptions import (X13NotFoundError,
-                                             IOWarning, X13Error,
-                                             X13Warning)
 
 __all__ = ["x13_arima_select_order", "x13_arima_analysis"]
 
-_binary_names = ('x13as.exe', 'x13as', 'x12a.exe', 'x12a',
-                 'x13as_ascii', 'x13as_html')
+_binary_names = ("x13as.exe", "x13as", "x12a.exe", "x12a", "x13as_ascii", "x13as_html")
 
 
 class _freq_to_period:
     def __getitem__(self, key):
-        if key.startswith('M'):
+        if key.startswith("M"):
             return 12
-        elif key.startswith('Q'):
+        elif key.startswith("Q"):
             return 4
-        elif key.startswith('W'):
+        elif key.startswith("W"):
             return 52
 
 
 _freq_to_period = _freq_to_period()
 
-_period_to_freq = {12: 'M', 4: 'Q'}
-_log_to_x12 = {True: 'log', False: 'none', None: 'auto'}
-_bool_to_yes_no = lambda x: 'yes' if x else 'no'  # noqa:E731
+_period_to_freq = {12: "M", 4: "Q"}
+_log_to_x12 = {True: "log", False: "none", None: "auto"}
+_bool_to_yes_no = lambda x: "yes" if x else "no"  # noqa:E731
 
 
 def _find_x12(x12path=None, prefer_x13=True):
@@ -72,8 +75,7 @@ def _find_x12(x12path=None, prefer_x13=True):
     for binary in _binary_names:
         x12 = os.path.join(x12path, binary)
         try:
-            subprocess.check_call(x12, stdout=subprocess.PIPE,
-                                  stderr=subprocess.PIPE)
+            subprocess.check_cal
```

## Moved from `brief.md`

## Files That May Need Changes

- `statsmodels/tsa/x13.py`
