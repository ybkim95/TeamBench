# Reference solution — GH952_plotly.py_2445

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH952_plotly.py_2445`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH952_plotly.py_2445/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CHANGELOG.md` (modified, +7/-0)
- `packages/python/plotly/codegen/__init__.py` (modified, +16/-11)
- `packages/python/plotly/plotly/graph_objects/__init__.py` (modified, +13/-9)
- `packages/python/plotly/plotly/graph_objs/__init__.py` (modified, +13/-9)
- `packages/python/plotly/plotly/missing_ipywidgets.py` (added, +15/-0)
- `packages/python/plotly/plotly/tests/test_core/test_figure_widget_backend/test_missing_ipywigets.py` (added, +38/-0)
- `packages/python/plotly/plotly/tests/test_core/test_figure_widget_backend/test_validate_no_frames.py` (modified, +7/-1)

## Diff Summary (What the Fix Changes)

### `packages/python/plotly/codegen/__init__.py`
```diff
@@ -269,14 +269,14 @@ def perform_codegen():
     optional_figure_widget_import = f"""
 if sys.version_info < (3, 7):
     try:
-        import ipywidgets
-        from distutils.version import LooseVersion
-        if LooseVersion(ipywidgets.__version__) >= LooseVersion('7.0.0'):
+        import ipywidgets as _ipywidgets
+        from distutils.version import LooseVersion as _LooseVersion
+        if _LooseVersion(_ipywidgets.__version__) >= _LooseVersion("7.0.0"):
             from ..graph_objs._figurewidget import FigureWidget
-        del LooseVersion
-        del ipywidgets
-    except ImportError:
-        pass
+        else:
+            raise ImportError()
+    except Exception:
+        from ..missing_ipywidgets import FigureWidget
 else:
     __all__.append("FigureWidget")
     orig_getattr = __getattr__
@@ -285,12 +285,17 @@ def __getattr__(import_name):
             try:
                 import ipywidgets
                 from distutils.version import LooseVersion
-                if LooseVersion(ipywidgets.__version__) >= LooseVersion('7.0.0'):
+
+                if LooseVersion(ipywidgets.__version__) >= LooseVersion("7.0.0"):
                     from ..graph_objs._figurewidget import FigureWidget
+
                     return FigureWidget
-            except ImportError:
-                    pass
-        
+                else:
+                    raise ImportError()
+            except Exception:
+                from ..missing_ipywidgets import FigureWidget
+                return FigureWidget
+
         return orig_getattr(import_name)
 """
     # ### __all__ ###
```

### `packages/python/plotly/plotly/graph_objects/__init__.py`
```diff
@@ -261,15 +261,15 @@
 
 if sys.version_info < (3, 7):
     try:
-        import ipywidgets
-        from distutils.version import LooseVersion
+        import ipywidgets as _ipywidgets
+        from distutils.version import LooseVersion as _LooseVersion
 
-        if LooseVersion(ipywidgets.__version__) >= LooseVersion("7.0.0"):
+        if _LooseVersion(_ipywidgets.__version__) >= _LooseVersion("7.0.0"):
             from ..graph_objs._figurewidget import FigureWidget
-        del LooseVersion
-        del ipywidgets
-    except ImportError:
-        pass
+        else:
+            raise ImportError()
+    except Exception:
+        from ..missing_ipywidgets import FigureWidget
 else:
     __all__.append("FigureWidget")
     orig_getattr = __getattr__
@@ -284,7 +284,11 @@ def __getattr__(import_name):
                     from ..graph_objs._figurewidget import FigureWidget
 
                     return FigureWidget
-            except ImportError:
-                pass
+                else:
+                    raise ImportError()
+            except Exception:
+                from ..missing_ipywidgets import FigureWidget
+
+                return FigureWidget
 
         return orig_getattr(import_name)
```

### `packages/python/plotly/plotly/graph_objs/__init__.py`
```diff
@@ -261,15 +261,15 @@
 
 if sys.version_info < (3, 7):
     try:
-        import ipywidgets
-        from distutils.version import LooseVersion
+        import ipywidgets as _ipywidgets
+        from distutils.version import LooseVersion as _LooseVersion
 
-        if LooseVersion(ipywidgets.__version__) >= LooseVersion("7.0.0"):
+        if _LooseVersion(_ipywidgets.__version__) >= _LooseVersion("7.0.0"):
             from ..graph_objs._figurewidget import FigureWidget
-        del LooseVersion
-        del ipywidgets
-    except ImportError:
-        pass
+        else:
+            raise ImportError()
+    except Exception:
+        from ..missing_ipywidgets import FigureWidget
 else:
     __all__.append("FigureWidget")
     orig_getattr = __getattr__
@@ -284,7 +284,11 @@ def __getattr__(import_name):
                     from ..graph_objs._figurewidget import FigureWidget
 
                     return FigureWidget
-            except ImportError:
-                pass
+                else:
+                    raise ImportError()
+            except Exception:
+                from ..missing_ipywidgets import FigureWidget
+
+                return FigureWidget
 
         return orig_getattr(import_name)
```

### `packages/python/plotly/plotly/missing_ipywidgets.py`
```diff
@@ -0,0 +1,15 @@
+from .basedatatypes import BaseFigure
+
+
+class FigureWidget(BaseFigure):
+    """
+    FigureWidget stand-in for use when ipywidgets is not installed. The only purpose
+    of this class is to provide something to import as
+    `plotly.graph_objs.FigureWidget` when ipywidgets is not installed. This class
+    simply raises an informative error message when the constructor is called
+    """
+
+    def __init__(self, *args, **kwargs):
+        raise ImportError(
+            "Please install ipywidgets>=7.0.0 to use the FigureWidget class"
+        )
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `packages/python/plotly/codegen/__init__.py`
- `packages/python/plotly/plotly/graph_objects/__init__.py`
- `packages/python/plotly/plotly/graph_objs/__init__.py`
- `packages/python/plotly/plotly/missing_ipywidgets.py`
