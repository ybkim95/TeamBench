# Reference solution — GH1106_plotly.py_466

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1106_plotly.py_466`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1106_plotly.py_466/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `plotly/graph_reference/default-schema.json` (modified, +132/-5)
- `plotly/offline/offline.py` (modified, +36/-43)
- `plotly/tests/test_optional/test_offline/test_offline.py` (modified, +2/-3)

## Diff Summary (What the Fix Changes)

### `plotly/offline/offline.py`
```diff
@@ -14,11 +14,10 @@
 
 import plotly
 from plotly import tools, utils
-from plotly.exceptions import PlotlyError
-
 
 try:
     import IPython
+    from IPython.display import HTML, display
     _ipython_imported = True
 except ImportError:
     _ipython_imported = False
@@ -30,9 +29,6 @@
     _matplotlib_imported = False
 
 
-__PLOTLY_OFFLINE_INITIALIZED = False
-
-
 def download_plotlyjs(download_url):
     warnings.warn('''
         `download_plotlyjs` is deprecated and will be removed in the
@@ -50,26 +46,36 @@ def get_plotlyjs():
 
 def init_notebook_mode():
     """
-    Initialize Plotly Offline mode in an IPython Notebook.
-    Run this function at the start of an IPython notebook
-    to load the necessary javascript files for creating
-    Plotly graphs with plotly.offline.iplot.
+    Initialize plotly.js in the browser if it hasn't been loaded into the DOM
+    yet. This is an idempotent method and can and should be called from any
+    offline methods that require plotly.js to be loaded into the notebook dom.
     """
-    if not tools._ipython_imported:
+    warnings.warn('''
+        `init_notebook_mode` is deprecated and will be removed in the
+        next release. Notebook mode is now automatically initialized when
+        notebook methods are invoked, so it is no
+        longer necessary to manually initialize.
+    ''', DeprecationWarning)
+
+    if not _ipython_imported:
         raise ImportError('`iplot` can only run inside an IPython Notebook.')
-    from IPython.display import HTML, display
 
-    global __PLOTLY_OFFLINE_INITIALIZED
-    if not __PLOTLY_OFFLINE_INITIALIZED:
-        display(HTML("<script type='text/javascript'>" +
-                     "define('plotly', function(require, exports, module) {" +
-                     get_plotlyjs() +
-                     "});" +
-                     "require(['plotly'], function(Plotly) {" +
-                     "window.Plotly = Plotly;" +
-                     "});" +
-                    
```

## Moved from `brief.md`

## Files That May Need Changes

- `plotly/offline/offline.py`
