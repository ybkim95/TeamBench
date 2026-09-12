# GH715_napari_7914: Prevent Shapes corruption when drawing tiny polygons with lasso — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/napari/napari/issues/7903
- Repo: https://github.com/napari/napari

## Issue Description

### 🐛 Bug Report

In a shapes layer, if I am very zoomed in and try to use the polygon lasso tool, I frequently get the following error

```python
TypeError                                 Traceback (most recent call last)
File ~/miniconda3/envs/edge-profiler/lib/python3.13/site-packages/superqt/utils/_throttler.py:286, in ThrottledCallable._set_future_result(self=<superqt.utils._throttler.ThrottledCallable object>)
    285 def _set_future_result(self):
--> 286     result = self._func(*self._args[: self._max_args], **self._kwargs)
        self._func = <function _weak_func.<locals>.weak_func at 0x2ca569580>
        self = <superqt.utils._throttler.ThrottledCallable object at 0x2ca392f90>
        self._args[: self._max_args] = (<MouseEvent blocked=False button=None buttons=[] delta=[0. 0.] handled=False is_dragging=False last_event=MouseEvent modifiers=() native=<PyQt5.QtGui.QMouseEvent object at 0x2ed3f4e60> pos=[480 862] press_event=None source=None sources=[] time=1746820974.4141362 type=mouse_move>,)
        self._kwargs = {}
        self._args = (<MouseEvent blocked=False button=None buttons=[] delta=[0. 0.] handled=False is_dragging=False last_event=MouseEvent modifiers=() native=<PyQt5.QtGui.QMouseEvent object at 0x2ed3f4e60> pos=[480 862] press_event=None source=None sources=[] time=1746820974.4141362 type=mouse_move>,)
        self._max_args = 1
    287     self._future.set_result(result)

File ~/miniconda3/envs/edge-profiler/lib/python3.13/site-packages/superqt/utils/_throttler.py:226, in _weak_func.<locals>.weak_func(*args=(<MouseEvent blocked=False button=None buttons=[]...urces=[] time=1746820974.4141362 type=mouse_move>,), **kwargs={})
    224 def weak_func(*args, **kwargs):
    225     if method := weak_method():
--> 226         return method(*args, **kwargs)
        method = <bound method VispyCanvas._on_mouse_move of <napari._vispy.canvas.VispyCanvas object at 0x2c3105a90>>
        args = (<MouseEvent blocked=False button=None buttons=[] delta=[0. 0.] handled=False is_dragging=False last_event=MouseEvent modifiers=() native=<PyQt5.QtGui.QMouseEvent object at 0x2ed3f4e60> pos=[480 862] press_event=None source=None sources=[] time=1746820974.4141362 type=mouse_move>,)
        kwargs = {}
    227     warnings.warn(
    228         "Method has been garbage collected", RuntimeWarning, stacklevel=2
    229     )

File ~/miniconda3/envs/edge-profiler/lib/python3.13/site-packages/napari/_vispy/canvas.py:453, in VispyCanvas._on_mouse_move(self=<napari._vispy.canvas.VispyCanvas object>, event=<MouseEvent blocked=False button=None buttons=[]...urces=[] time=1746820974.4141362 type=mouse_move>)
    441 def _on_mouse_move(self, event: MouseEvent) -> None:
    442     """Called whenever mouse moves over canvas.
    443 
    444     Parameters
   (...)
    451     None
    452     """
--> 453     self._process_mouse_event(mouse_move_callbacks, event)
        event = <MouseEvent blocked=False button=None buttons=[] delta=[0. 0.] handled=False is_dragging=False last_event=MouseEvent modifiers=() native=<PyQt5.QtGui.QMouseEvent object at 0x2ed3f4e60> pos=[480 862] press_event=None source=None sources=[] time=1746820974.4141362 type=mouse_move>
        self = <napari._vispy.canvas.VispyCanvas object at 0x2c3105a90>

File ~/miniconda3/envs/edge-profiler/lib/python3.13/site-packages/napari/_vispy/canvas.py:414, in VispyCanvas._process_mouse_event(self=<napari._vispy.canvas.VispyCanvas object>, mouse_callbacks=<function mouse_move_callbacks>, event=<MouseEvent blocked=False button=None buttons=[]...urces=[] time=1746820974.4141362 type=mouse_move>)
    412 layer = self.viewer.layers.selection.active
    413 if layer is not None:
--> 414     mouse_callbacks(layer, read_only_event)
        read_only_event = <ReadOnlyWrapper at 0x2ebb4ecc0 for NapariMouseEvent at 0x2ecfa7850>
        layer = <Shapes layer 'Shapes' at 0x2d1f78ec0>
        mouse_callbacks = <function mouse_move_callbacks at 0x2ad72fc40>

File ~/miniconda3/envs/edge-profiler/lib/python3.13/site-packages/napari/utils/interactions.py:173, in mouse_move_callbacks(obj=<Shapes layer 'Shapes'>, event=<ReadOnlyWrapper at 0x2ebb4ecc0 for NapariMouseEvent>)
    170 if not event.is_dragging:
    171     # if not dragging simply call the mouse move callbacks
    172     for mouse_move_func in obj.mouse_move_callbacks:
--> 173         mouse_move_func(obj, event)
        mouse_move_func = <function polygon_creating at 0x2c0837740>
        event = <ReadOnlyWrapper at 0x2ebb4ecc0 for NapariMouseEvent at 0x2ecfa7850>
        obj = <Shapes layer 'Shapes' at 0x2d1f78ec0>
    175 # for each drag callback get the current generator
    176 for func, gen in tuple(obj._mouse_drag_gen.items()):
    177     # save the event current event

File ~/miniconda3/envs/edge-profiler/lib/python3.13/site-packages/napari/layers/shapes/_shapes_mouse_bindings.py:421, in polygon_creating(layer=<Shapes layer 'Shapes'>, event=<ReadOnlyWrapper at 0x2ebb4ecc0 for NapariMouseEvent>)
    417 if layer._mode in [Mode.ADD_POLYGON_LASSO, Mode.ADD_PATH]:
    418     index = layer._moving_value[0]
    420     position_diff = np.linalg.norm(
--> 421         event.pos - layer._last_cursor_position
        np.linalg.norm = <function norm at 0x101f768b0>
        np.linalg = <module 'numpy.linalg' from '/Users/elowskyc/miniconda3/envs/edge-profiler/lib/python3.13/site-packages/numpy/linalg/__init__.py'>
        np = <module 'numpy' from '/Users/elowskyc/miniconda3/envs/edge-profiler/lib/python3.13/site-packages/numpy/__init__.py'>
        layer = <Shapes layer 'Shapes' at 0x2d1f78ec0>
        event = <ReadOnlyWrapper at 0x2ebb4ecc0 for NapariMouseEvent at 0x2ecfa7850>
        layer._last_cursor_position = None
    422     )
    423     if (
    424         position_diff
    425         > get_settings().experimental.lasso_vertex_distance
    426     ):
    427         add_vertex_to_path(layer, event, index, coordinates, None)

TypeError: unsupported operand type(s) for -: 'int' and 'NoneType'
```

### 💡 Steps to Reproduce

1) Create a shapes layer
2) Zoom in a lot
3) Try to create a shape using the polygon lasso tool

### 💡 Expected Behavior

I expect the shape to be created without error 

### 🌎 Environment

napari: 0.6.0
Platform: macOS-13.6.3-arm64-arm-64bit-Mach-O
System: MacOS 13.6.3
Python: 3.13.1 | packaged by conda-forge | (main, Jan 13 2025, 09:45:31) [Clang 18.1.8 ]
Qt: 5.15.14
PyQt5: 5.15.11
NumPy: 2.2.2
SciPy: 1.15.1
Dask: 2025.1.0
VisPy: 0.14.3
magicgui: 0.10.0
superqt: 0.6.7
in-n-out: 0.2.1
app-model: 0.3.1
psygnal: 0.12.0
npe2: 0.7.8
pydantic: 2.10.6

OpenGL:
  - PyOpenGL: 3.1.9
  - GL version:  2.1 Metal - 83.1
  - MAX_TEXTURE_SIZE: 16384
  - GL_MAX_3D_TEXTURE_SIZE: 2048

Screens:
  - screen 1: resolution 1920x1080, scale 2.0

Optional:
  - numba not installed
  - triangle not installed
  - napari-plugin-manager not installed
  - bermuda not installed
  - PartSegCore not installed

Experimental Settings:
  - Async: False
  - Autoswap buffers: False
  - Triangulation backend: Fastest available

Settings path:
  - /Users/elowskyc/Library/Application Support/napari/edge-profiler_fbe85e2511dc35ac6ea40e4bcd91a295508afde1/settings.yaml
Plugins:
  - edge-profiler: 0.0.1 (2 contributions)
  - napari: 0.6.0 (81 contributions)
  - napari-console: 0.1.3 (0 contributions)
  - napari-svg: 0.2.1 (2 contributions)

### 💡 Additional Context

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I am able to reproduce. Thank you for this bug report!
I am at a VERY high zoom to reproduce this! This appears to happen on all backends, but I haven't thoroughly tested. The below is what the lasso looks like when the error occurs (it stays stuck in this state until interaction)

![Image](https://github.com/user-attachments/assets/a292be4e-204c-442f-8ced-2ced01f6f721)

A shape drawn like this will work, so it's some kind of issue with connecting the ends.

![Image](https://github.com/user-attachments/assets/8165692a-e765-4a9f-922c-21ff6eec92e5)

There is an initial error that occurs before [user]'s traceback. Which I'll past below. 

```python
---------------------------------------------------------------------------
ValueError                                Traceback (most recent call last)
File ~\AppData\Roaming\uv\tools\napari\Lib\site-packages\vispy\app\backends\_qt.py:506, in QtBaseCanvasBackend.mouseReleaseEvent(self=<vispy.app.backends._qt.CanvasBackendDesktop object>, ev=<PyQt5.QtGui.QMouseEvent object>)
    504 if self._vispy_canvas is None:
    505     return
--> 506 self._vispy_mouse_release(
        self = <vispy.app.backends._qt.CanvasBackendDesktop object at 0x0000023F380BE830>
        ev = <PyQt5.QtGui.QMouseEvent object at 0x0000023F4443B880>
        BUTTONMAP = {0: 0, 1: 1, 2: 2, 4: 3, 8: 4, 16: 5}
    507     native=ev,
    508     pos=_get_event_xy(ev),
    509     button=BUTTONMAP[ev.button()],
    510     modifiers=self._modifiers(ev),
    511 )

File ~\AppData\Roaming\uv\tools\napari\Lib\site-packages\vispy\app\base.py:224, in BaseCanvasBackend._vispy_mouse_release(self=<vispy.app.backends._qt.CanvasBackendDesktop object>, **kwargs={'button': 1, 'buttons': [1], 'last_event': <MouseEvent blocked=False button=1 buttons=[1] d...urces=[] time=1746822681.7455013 type=mouse_move>, 'last_mouse_press': None, 'modifiers': (), 'native': <PyQt5.QtGui.QMouseEvent object>, 'pos': (790, 551), 'press_event': <MouseEvent blocked=False button=1 buttons=[1] d...rces=[] time=1746822680.1494517 type=mouse_press>})
    220 def _vispy_mouse_release(self, **kwargs):
    221     # default method for delivering mouse release events to the canvas
    222     kwargs.update(self._vispy_mouse_data)
--> 224     ev = self._vispy_canvas.events.mouse_release(**kwargs)
        self._vispy_canvas.events.mouse_release = <vispy.util.event.EventEmitter object at 0x0000023F3856DFD0>
        kwargs = {'native': <PyQt5.QtGui.QMouseEvent object at 0x0000023F4443B880>, 'pos': (790, 551), 'button': 1, 'modifiers': (), 'buttons': [1], 'press_event': <MouseEvent blocked=False button=1 buttons=[1] delta=[0. 0.] handled=False is_dragging=False last_event=MouseEvent modifiers=() native=<PyQt5.QtGui.QMouseEvent object at 0x0000023F4443B880> pos=[804 446] press_event=None source=None sources=[] time=1746822680.1494517 type=mouse_press>, 'last_event': <MouseEvent blocked=False button=1 buttons=[1] delta=[0. 0.] handled=False is_dragging=True last_event=MouseEvent modifiers=() native=<PyQt5.QtGui.QMouseEvent object at 0x0000023F4443B880> pos=[788 554] press_event=MouseEvent source=None sources=[] time=1746822681.7455013 type=mouse_move>, 'last_mouse_press': None}
        self = <vispy.app.backends._qt.CanvasBackendDesktop object at 0x0000023F380BE830>
        self._vispy_canvas.events = <vispy.util.event.EmitterGroup object at 0x0000023F3812B7D0>
        self._vispy_canvas = <NapariSceneCanvas (PyQt5) at 0x23f385645d0>
    225     if (self._vispy_mouse_data['press_event']
    226             and self._vispy_mouse_data['press_event'].button == ev.button):
    227         self._vispy_mouse_data['press_event'] = None

File ~\AppData\Roaming\uv\tools\napari\Lib\site-packages\vispy\util\event.py:453, in EventEmitter.__call__(self=<vispy.util.event.EventEmitter object>, *args=(), **kwargs={'button': 1, 'buttons': [1], 'last_event': <MouseEvent blocked=False button=1 buttons=[1] d...urces=[] time=1746822681.7455013 type=mouse_move>, 'last_mouse_press': None, 'modifiers': (), 'native': <PyQt5.QtGui.QMouseEvent object>, 'pos': (790, 551), 'press_event': <MouseEvent blocked=False button=1 buttons=[1] d...rces=[] time=1746822680.1494517 type=mouse_press>})
    450 if self._emitting > 1:
    451     raise RuntimeError('EventEmitter loop detected!')
--> 453 self._invoke_callback(cb, event)
        event = <MouseEvent blocked=False button=1 buttons=[1] delta=[0. 0.] handled=False is_dragging=True last_event=MouseEvent modifiers=() native=<PyQt5.QtGui.QMouseEvent object at 0x0000023F4443B880> pos=[790 551] press_event=MouseEvent source=None sources=[] time=1746822681.8511236 type=mouse_release>
        self = <vispy.util.event.EventEmitter object at 0x0000023F3856DFD0>
        cb = <bound method VispyCanvas._on_mouse_release of <napari._vispy.canvas.VispyCanvas object at 0x0000023F38529AD0>>
    454 if event.blocked:
    455     break

File ~\AppData\Roaming\uv\tools\napari\Lib\site-packages\vispy\util\event.py:471, in EventEmitter._invoke_callback(self=<vispy.util.event.EventEmitter object>, cb=<bound method VispyCanvas._on_mouse_release of <napari._vispy.canvas.VispyCanvas object>>, event=<MouseEvent blocked=False button=1 buttons=[1] d...es=[] time=1746822681.8511236 type=mouse_release>)
    469     cb(event)
    470 except Exception:
--> 471     _handle_exception(self.ignore_callback_errors,
        self = <vispy.util.event.EventEmitter object at 0x0000023F3856DFD0>
        cb = <bound method VispyCanvas._on_mouse_release of <napari._vispy.canvas.VispyCanvas object at 0x0000023F38529AD0>>
        event = <MouseEvent blocked=False button=1 buttons=[1] delta=[0. 0.] handled=False is_dragging=True last_event=MouseEvent modifiers=() native=<PyQt5.QtGui.QMouseEvent object at 0x0000023F4443B880> pos=[790 551] press_event=MouseEvent source=None sources=[] time=1746822681.8511236 type=mouse_release>
        (cb, event) = (<bound method VispyCanvas._on_mouse_release of <napari._vispy.canvas.VispyCanvas object at 0x0000023F38529AD0>>, <MouseEvent blocked=False button=1 buttons=[1] delta=[0. 0.] handled=False is_dragging=True last_event=MouseEvent modifiers=() native=<PyQt5.QtGui.QMouseEvent object at 0x0000023F4443B880> pos=[790 551] press_event=MouseEvent source=None sources=[] time=1746822681.8511236 type=mouse_release>)
    472                       self.print_callback_errors,
    473                       self, cb_event=(cb, event))

File ~\AppData\Roaming\uv\tools\napari\Lib\site-packages\vispy\util\event.py:469, in EventEmitter._invoke_callback(self=<vispy.util.event.EventEmitter object>, cb=<bound method VispyCanvas._on_mouse_release of <napari._vispy.canvas.VispyCanvas object>>, event=<MouseEvent blocked=False button=1 buttons=[1] d...es=[] time=1746822681.8511236 type=mouse_release>)
    467 def _invoke_callback(self, cb, event):
    468     try:
--> 469         cb(event)
        cb = <bound method VispyCanvas._on_mouse_release of <napari._vispy.canvas.VispyCanvas object at 0x0000023F38529AD0>>
        event = <MouseEvent blocked=False button=1 buttons=[1] delta=[0. 0.] handled=False is_dragging=True last_event=MouseEvent modifiers=() native=<PyQt5.QtGui.QMouseEvent object at 0x0000023F4443B880> pos=[790 551] press_event=MouseEvent source=None sources=[] time=1746822681.8511236 type=mouse_release>
    470     except Exception:
    471         _handle_exception(self.ignore_callback_errors,
    472                           self.print_callback_errors,
    473                           self, cb_event=(cb, event))

File ~\Documents\Github\napari\napari\_vispy\canvas.py:481, in VispyCanvas._on_mouse_release(self=<napari._vispy.canvas.VispyCanvas object>, event=<MouseEvent blocked=False button=1 buttons=[1] d...es=[] time=1746822681.8511236 type=mouse_release>)
    469 def _on_mouse_release(self, event: MouseEvent) -> None:
    470     """Called whenever mouse released in canvas.
    471 
    472     Parameters
   (...)
    479     None
    480     """
--> 481     self._process_mouse_event(mouse_release_callbacks, event)
        event = <MouseEvent blocked=False button=1 buttons=[1] delta=[0. 0.] handled=False is_dragging=True last_event=MouseEvent modifiers=() native=<PyQt5.QtGui.QMouseEvent object at 0x0000023F4443B880> pos=[790 551] press_event=MouseEvent source=None sources=[] time=1746822681.8511236 type=mouse_release>
        self = <napari._vispy.canvas.VispyCanvas object at 0x0000023F38529AD0>

File ~\Documents\Github\napari\napari\_vispy\canvas.py:414, in VispyCanvas._process_mouse_event(self=<napari._vispy.canvas.VispyCanvas object>, mouse_callbacks=<function mouse_release_callbacks>, event=<MouseEvent blocked=False button=1 buttons=[1] d...es=[] time=1746822681.8511236 type=mouse_release>)
    412 layer = self.viewer.layers.selection.active
    413 if layer is not None:
--> 414     mouse_callbacks(layer, read_only_event)
        read_only_event = <ReadOnlyWrapper at 0x0000023F48E9F2C0 for NapariMouseEvent at 0x0000023F51E23F90>
        layer = <Shapes layer 'Shapes' at 0x23f48de3e10>
        mouse_callbacks = <function mouse_release_callbacks at 0x0000023F33DF3560>

File ~\Documents\Github\napari\napari\utils\interactions.py:220, in mouse_release_callbacks(obj=<Shapes layer 'Shapes'>, event=<ReadOnlyWrapper at 0x0000023F48E9F2C0 for NapariMouseEvent>)
    217 obj._persisted_mouse_event[gen].__wrapped__ = event
    218 with contextlib.suppress(StopIteration):
    219     # Run last part of the function to trigger release event
--> 220     next(gen)
        gen = <generator object add_path_polygon_lasso at 0x0000023F50C7D5D0>
    221 # Finally delete the generator and stored event
    222 del obj._mouse_drag_gen[func]

File ~\Documents\Github\napari\napari\layers\shapes\_shapes_mouse_bindings.py:355, in add_path_polygon_lasso(layer=<Shapes layer 'Shapes'>, event=<ReadOnlyWrapper at 0x0000023F48DC8500 for ReadOnlyWrapper>)
    353     # If number of vertices is higher than 2, tablet draw mode is assumed and shape is finished upon mouse release
    354     if len(vertices) > 2:
--> 355         layer._finish_drawing()
        layer = <Shapes layer 'Shapes' at 0x23f48de3e10>
    356 else:
    357     # This code block is responsible for finishing drawing in mouse draw mode
    358     layer._finish_drawing()

File ~\Documents\Github\napari\napari\layers\shapes\shapes.py:2657, in Shapes._finish_drawing(self=<Shapes layer 'Shapes'>, event=None)
   2652         else:
   2653             vertices = rdp(
   2654                 vertices,
   2655                 epsilon=get_settings().experimental.rdp_epsilon,
   2656             )
-> 2657             self._data_view.edit(
        self = <Shapes layer 'Shapes' at 0x23f48de3e10>
        self._data_view = <napari.layers.shapes._shape_list.ShapeList object at 0x0000023F4EB4CD50>
        index = 0
        vertices = array([[ 29.     ,  89.22366, 110.88003],
       [ 29.     ,  89.30281, 110.8683 ]], dtype=float32)
        shape_classes = {<ShapeType.RECTANGLE: 'rectangle'>: <class 'napari.layers.shapes._shapes_models.rectangle.Rectangle'>, <ShapeType.ELLIPSE: 'ellipse'>: <class 'napari.layers.shapes._shapes_models.ellipse.Ellipse'>, <ShapeType.LINE: 'line'>: <class 'napari.layers.shapes._shapes_models.line.Line'>, <ShapeType.PATH: 'path'>: <class 'napari.layers.shapes._shapes_models.path.Path'>, <ShapeType.POLYGON: 'polygon'>: <class 'napari.layers.shapes._shapes_models.polygon.Polygon'>}
        ShapeType.POLYGON = <ShapeType.POLYGON: 'polygon'>
        ShapeType = <enum 'ShapeType'>
   2658                 index,
   2659                 vertices[:-1],
   2660                 new_type=shape_classes[ShapeType.POLYGON],
   2661             )
   2662 # handles the case that
   2663 if index is not None:

File ~\Documents\Github\napari\napari\layers\shapes\_shape_list.py:1058, in ShapeList.edit(self=<napari.layers.shapes._shape_list.ShapeList object>, index=0, data=array([[ 29.     ,  89.22366, 110.88003]], dtype=float32), face_color=None, edge_color=None, new_type=<class 'napari.layers.shapes._shapes_models.polygon.Polygon'>)
   1056     else:
   1057         shape_cls = new_type
-> 1058     shape = shape_cls(
        shape_cls = <class 'napari.layers.shapes._shapes_models.polygon.Polygon'>
        data = array([[ 29.     ,  89.22366, 110.88003]], dtype=float32)
        cur_shape = <napari.layers.shapes._shapes_models.path.Path object at 0x0000023F51E54210>
   1059         data,
   1060         edge_width=cur_shape.edge_width,
   1061         z_index=cur_shape.z_index,
   1062         dims_order=cur_shape.dims_order,
   1063     )
   1064 else:
   1065     shape = self.shapes[index]

File ~\Documents\Github\napari\napari\layers\shapes\_shapes_models\polygon.py:30, in Polygon.__init__(self=<napari.layers.shapes._shapes_models.polygon.Polygon object>, data=array([[ 29.     ,  89.22366, 110.88003]], dtype=float32), edge_width=1, z_index=0, dims_order=(0, 1, 2), ndisplay=2, interpolation_order=1)
     20 def __init__(
     21     self,
     22     data,
   (...)
     28     interpolation_order=1,
     29 ) -> None:
---> 30     super().__init__(
        data = array([[ 29.     ,  89.22366, 110.88003]], dtype=float32)
        edge_width = 1
        z_index = 0
        dims_order = (0, 1, 2)
        ndisplay = 2
        interpolation_order = 1
     31         data=data,
     32         edge_width=edge_width,
     33         z_index=z_index,
     34         dims_order=dims_order,
     35         ndisplay=ndisplay,
     36         closed=True,
     37         filled=True,
     38         name='polygon',
     39         interpolation_order=interpolation_order,
     40     )

File ~\Documents\Github\napari\napari\layers\shapes\_shapes_models\_polygon_base.py:64, in PolygonBase.__init__(self=<napari.layers.shapes._shapes_models.polygon.Polygon object>, data=array([[ 29.     ,  89.22366, 110.88003]], dtype=float32), edge_width=1, z_index=0, dims_order=(0, 1, 2), ndisplay=2, filled=True, closed=True, name='polygon', interpolation_order=1, interpolation_sampling=50)
     61 self.interpolation_order = interpolation_order
     62 self.interpolation_sampling = interpolation_sampling
---> 64 self.data = data
        data = array([[ 29.     ,  89.22366, 110.88003]], dtype=float32)
        self = <napari.layers.shapes._shapes_models.polygon.Polygon object at 0x0000023F48E4A490>

File ~\Documents\Github\napari\napari\layers\shapes\_shapes_models\_polygon_base.py:79, in PolygonBase.data(self=<napari.layers.shapes._shapes_models.polygon.Polygon object>, data=array([[ 29.     ,  89.22366, 110.88003]], dtype=float32))
     76     self._dims_order = list(range(data.shape[1]))
     78 if len(data) < 2:
---> 79     raise ValueError(
        trans = <napari.utils.translations.TranslationBundle object at 0x0000023F2C453950>
        data = array([[ 29.     ,  89.22366, 110.88003]], dtype=float32)
     80         trans._(
     81             'Shape needs at least two unique vertices, {number} provided.',
     82             deferred=True,
     83             number=len(data),
     84         )
     85     )
     87 self._data = data
     88 self._bounding_box = np.array(
     89     [
     90         np.min(data, axis=0),
     91         np.max(data, axis=0),
     92     ]
     93 )

ValueError: Shape needs at least two unique vertices, 1 provided.
```

### Comment 2 ([user]):

Yeah I can reproduce as well, but only when essentially trying to draw a polygon on a single pixel, so seems a bit of a corner case -- [user] do you have a real use case that triggers this? can you share the image and use case?
The other tools do work at single-pixel resolution, so it isn't a Shapes thing, but specific to the tool.

### Comment 3 ([user]):

It is not so much of a use case that it is needed for, but more of an inconvenience for users of the plugin that I am writing. Occasionally they create these accidental shapes with the polygon lasso tool and it disrupts their workflow.

I am even able to reproduce the error when I am not so zoomed in. See the image below. This seems to be happening quite often for our users.

<img width="316" alt="Image" src="https://github.com/user-attachments/assets/0688b9c8-24f4-4fa7-aa2c-b33bd5c833c8" />

### Comment 4 ([user]):

Oh, I can reproduce that -- different traceback too!
So if you just misclick and make a short-ish straight line with the lasso tool, then you can also break the layer with the same error form the OP. So there are two different issues: the high zoom and the line misclick.
```python
---------------------------------------------------------------------------
TypeError                                 Traceback (most recent call last)
File ~/micromamba/envs/napari-dev/lib/python3.13/site-packages/superqt/utils/_throttler.py:286, in ThrottledCallable._set_future_result(self=<superqt.utils._throttler.ThrottledCallable object>)
    285 def _set_future_result(self):
--> 286     result = self._func(*self._args[: self._max_args], **self._kwargs)
        self._func = <function _weak_func.<locals>.weak_func at 0x160d30720>
        self = <superqt.utils._throttler.ThrottledCallable object at 0x161066210>
        self._args[: self._max_args] = (<MouseEvent blocked=False button=None buttons=[] delta=[0. 0.] handled=False is_dragging=False last_event=MouseEvent modifiers=() native=<PyQt6.QtGui.QMouseEvent object at 0x16e5487d0> pos=[802 596] press_event=None source=None sources=[] time=1746824522.6337311 type=mouse_move>,)
        self._kwargs = {}
        self._args = (<MouseEvent blocked=False button=None buttons=[] delta=[0. 0.] handled=False is_dragging=False last_event=MouseEvent modifiers=() native=<PyQt6.QtGui.QMouseEvent object at 0x16e5487d0> pos=[802 596] press_event=None source=None sources=[] time=1746824522.6337311 type=mouse_move>,)
        self._max_args = 1    287     self._future.set_result(result)

File ~/micromamba/envs/napari-dev/lib/python3.13/site-packages/superqt/utils/_throttler.py:226, in _weak_func.<locals>.weak_func(*args=(<MouseEvent blocked=False button=None buttons=[]...urces=[] time=1746824522.6337311 type=mouse_move>,), **kwargs={})
    224 def weak_func(*args, **kwargs):
    225     if method := weak_method():
--> 226         return method(*args, **kwargs)
        method = <bound method VispyCanvas._on_mouse_move of <napari._vispy.canvas.VispyCanvas object at 0x14bad42f0>>
        args = (<MouseEvent blocked=False button=None buttons=[] delta=[0. 0.] handled=False is_dragging=False last_event=MouseEvent modifiers=() native=<PyQt6.QtGui.QMouseEvent object at 0x16e5487d0> pos=[802 596] press_event=None source=None sources=[] time=1746824522.6337311 type=mouse_move>,)
        kwargs = {}    227     warnings.warn(
    228         "Method has been garbage collected", RuntimeWarning, stacklevel=2
    229     )

File ~/Documents/dev/napari/napari/_vispy/canvas.py:458, in VispyCanvas._on_mouse_move(self=<napari._vispy.canvas.VispyCanvas object>, event=<MouseEvent blocked=False button=None buttons=[]...urces=[] time=1746824522.6337311 type=mouse_move>)
    446 def _on_mouse_move(self, event: MouseEvent) -> None:
    447     """Called whenever mouse moves over canvas.
    448 
    449     Parameters
   (...)    456     None
    457     """
--> 458     self._process_mouse_event(mouse_move_callbacks, event)
        event = <MouseEvent blocked=False button=None buttons=[] delta=[0. 0.] handled=False is_dragging=False last_event=MouseEvent modifiers=() native=<PyQt6.QtGui.QMouseEvent object at 0x16e5487d0> pos=[802 596] press_event=None source=None sources=[] time=1746824522.6337311 type=mouse_move>
        self = <napari._vispy.canvas.VispyCanvas object at 0x14bad42f0>
File ~/Documents/dev/napari/napari/_vispy/canvas.py:419, in VispyCanvas._process_mouse_event(self=<napari._vispy.canvas.VispyCanvas object>, mouse_callbacks=<function mouse_move_callbacks>, event=<MouseEvent blocked=False button=None buttons=[]...urces=[] time=1746824522.6337311 type=mouse_move>)
    417 layer = self.viewer.layers.selection.active
    418 if layer is not None:
--> 419     mouse_callbacks(layer, read_only_event)
        read_only_event = <ReadOnlyWrapper at 0x32791f680 for NapariMouseEvent at 0x3275b4350>
        layer = <Shapes layer 'Shapes' at 0x16e0b3ed0>
        mouse_callbacks = <function mouse_move_callbacks at 0x14169fb00>
File ~/Documents/dev/napari/napari/utils/interactions.py:173, in mouse_move_callbacks(obj=<Shapes layer 'Shapes'>, event=<ReadOnlyWrapper at 0x32791f680 for NapariMouseEvent>)
    170 if not event.is_dragging:
    171     # if not dragging simply call the mouse move callbacks
    172     for mouse_move_func in obj.mouse_move_callbacks:
--> 173         mouse_move_func(obj, event)
        mouse_move_func = <function polygon_creating at 0x143ab8f40>
        event = <ReadOnlyWrapper at 0x32791f680 for NapariMouseEvent at 0x3275b4350>
        obj = <Shapes layer 'Shapes' at 0x16e0b3ed0>    175 # for each drag callback get the current generator
    176 for func, gen in tuple(obj._mouse_drag_gen.items()):
    177     # save the event current event

File ~/Documents/dev/napari/napari/layers/shapes/_shapes_mouse_bindings.py:421, in polygon_creating(layer=<Shapes layer 'Shapes'>, event=<ReadOnlyWrapper at 0x32791f680 for NapariMouseEvent>)
    417 if layer._mode in [Mode.ADD_POLYGON_LASSO, Mode.ADD_PATH]:
    418     index = layer._moving_value[0]
    420     position_diff = np.linalg.norm(
--> 421         event.pos - layer._last_cursor_position
        np.linalg.norm = <function norm at 0x107973130>
        np.linalg = <module 'numpy.linalg' from '/Users/sobolp/micromamba/envs/napari-dev/lib/python3.13/site-packages/numpy/linalg/__init__.py'>
        np = <module 'numpy' from '/Users/sobolp/micromamba/envs/napari-dev/lib/python3.13/site-packages/numpy/__init__.py'>
        layer = <Shapes layer 'Shapes' at 0x16e0b3ed0>
        event = <ReadOnlyWrapper at 0x32791f680 for NapariMouseEvent at 0x3275b4350>
        layer._last_cursor_position = None    422     )
    423     if (
    424         position_diff
    425         > get_settings().experimental.lasso_vertex_distance
    426     ):
    427         add_vertex_to_path(layer, event, index, coordinates, None)

TypeError: unsupported operand type(s) for -: 'int' and 'NoneType'
```

### Comment 5 ([user]):

Lots of bugs coming in from 0.6.0… 😅 Thanks [user] for the bug report!

We'll probably be making a few bugfix releases in quick succession. I've added this to 0.6.1 but it might get bumped to 0.6.2 depending on developer time. But I do consider it a high priority to fix. 🙏

### Comment 6 ([user]):

Juan just reproduced on 0.5.6
Probably dates to original lasso implementation

### Comment 7 ([user]):

Ok it has to do with the RDP epsilon. Setting it to 0 resolves the issue for me:

![napari RDP epsilon settings](https://github.com/user-attachments/assets/3eac6aba-d3cf-4608-b452-952797d911f3)

[user] can you verify?

[user] maybe you have some ideas on how to make the RDP code more robust to variations in the total shape size?

### Comment 8 ([user]):

Setting RDP to 0.10 also worked for me, if you want a more 'simplified' shape, compared to 0.00 keeping all the vertices.

### Comment 9 ([user]):

Since there is a workaround (now verified by both [user] and me), I'm going to move this to the next release milestone. We should still find a way to make the lasso more robust to weird scales.

### Comment 10 ([user]):

Ok. So the real bug stacktrace is here

```python
Traceback (most recent call last):
  File "/home/czaki/.pyenv/versions/napari_3.11/lib/python3.11/site-packages/vispy/app/backends/_qt.py", line 509, in mouseReleaseEvent
    vispy_event = self._vispy_mouse_release(
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/czaki/.pyenv/versions/napari_3.11/lib/python3.11/site-packages/vispy/app/base.py", line 224, in _vispy_mouse_release
    ev = self._vispy_canvas.events.mouse_release(**kwargs)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/czaki/.pyenv/versions/napari_3.11/lib/python3.11/site-packages/vispy/util/event.py", line 453, in __call__
    self._invoke_callback(cb, event)
  File "/home/czaki/.pyenv/versions/napari_3.11/lib/python3.11/site-packages/vispy/util/event.py", line 471, in _invoke_callback
    _handle_exception(self.ignore_callback_errors,
  File "/home/czaki/.pyenv/versions/napari_3.11/lib/python3.11/site-packages/vispy/util/event.py", line 469, in _invoke_callback
    cb(event)
  File "/home/czaki/Projekty/napari/napari/_vispy/canvas.py", line 481, in _on_mouse_release
    self._process_mouse_event(mouse_release_callbacks, event)
  File "/home/czaki/Projekty/napari/napari/_vispy/canvas.py", line 414, in _process_mouse_event
    mouse_callbacks(layer, read_only_event)
  File "/home/czaki/Projekty/napari/napari/utils/interactions.py", line 220, in mouse_release_callbacks
    next(gen)
  File "/home/czaki/Projekty/napari/napari/layers/shapes/_shapes_mouse_bindings.py", line 355, in add_path_polygon_lasso
    layer._finish_drawing()
  File "/home/czaki/Projekty/napari/napari/layers/shapes/shapes.py", line 2657, in _finish_drawing
    self._data_view.edit(
  File "/home/czaki/Projekty/napari/napari/layers/shapes/_shape_list.py", line 1058, in edit
    shape = shape_cls(
            ^^^^^^^^^^
  File "/home/czaki/Projekty/napari/napari/layers/shapes/_shapes_models/polygon.py", line 30, in __init__
    super().__init__(
  File "/home/czaki/Projekty/napari/napari/layers/shapes/_shapes_models/_polygon_base.py", line 64, in __init__
    self.data = data
    ^^^^^^^^^
  File "/home/czaki/Projekty/napari/napari/layers/shapes/_shapes_models/_polygon_base.py", line 79, in data
    raise ValueError(
ValueError: Shape needs at least two unique vertices, 1 provided.
```

It means that after points deduplication, there is a single point on line. 

But the `_last_cursor_position` is aleready set to None in line 2632 
https://github.com/napari/napari/blob/366ceed04fb6feeed9322d75fcf518097b30c90a/napari/layers/shapes/shapes.py#L2632
(on stacktrace we are in line 2657)
https://github.com/napari/napari/blob/366ceed04fb6feeed9322d75fcf518097b30c90a/napari/layers/shapes/shapes.py#L2657

And `is_creating` disabled should be disabled in line 2670

https://github.com/napari/napari/blob/366ceed04fb6feeed9322d75fcf518097b30c90a/napari/layers/shapes/shapes.py#L2670

All other stactraces are reporting, the broken state.

Will try to find time to fix today.

## PR Review Comments

**[user]** on `napari/layers/shapes/shapes.py`:

Whether we end up using show_warning, warnings.warn, or logging.log (could we hook up log warnings and errors to our notifications?), here is my suggestion for the message:

> Polygons must have three vertices. Lasso polygons are simplified using an algorithm called RDP, which may cause polygons smaller than the *RDP epsilon parameter* to disappear entirely. You can change this parameter in napari > Settings > Experimental > RDP epsilon.

Maybe this is better in the docs and then we can just link to the docs:

> Simplified polygon has too few vertices. See [link] for details.

**[user]** on `napari/layers/shapes/shapes.py`:

```suggestion
                                'Polygons must have three or more vertices. '
                                'Lasso polygons are simplified using the '
                                'RDP algorithm, which may cause polygons '
                                'smaller than RDP epsilon to disappear. If  '
                                'you face issues drawing small polygons, '
                                'try reducing napari > Settings > '
                                'Experimental > RDP epsilon. '
```
![image](https://github.com/user-attachments/assets/0b165cae-ebff-4455-a8a3-77e43553cfae)

This works for me

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
