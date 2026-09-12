# GH646_napari_6965: Add cachable context mapping — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/napari/napari/issues/6643
- Repo: https://github.com/napari/napari

## Issue Description

### 🐛 Bug Report

If you add a shapes layer and draw some shapes and then right-click to try to Convert to Labels, the option is greyed out. 

<img width="712" alt="image" src="https://github.com/napari/napari/assets/76622105/e68e4b47-6446-4e92-b619-77d69dc73ff6">

This makes it hard to discover the usability of this menu option.
Deselecting and reselecting the layer makes it show properly.

<img width="326" alt="image" src="https://github.com/napari/napari/assets/76622105/83969681-6be7-4900-9957-8d326b7e03bc">

### 💡 Steps to Reproduce

1. Add a new Shapes layer
2. Draw a shape
3. Right-click to get the layer list contextual menu

### 💡 Expected Behavior

The Convert option should be available regardless if the layer was re-selected.

### 🌎 Environment

napari: 0.5.0a2.dev543+gad78ee21a
Platform: macOS-13.3.1-arm64-arm-64bit
System: MacOS 13.3.1
Python: 3.11.7 | packaged by conda-forge | (main, Dec 23 2023, 14:38:07) [Clang 16.0.6 ]
Qt: 6.6.1
PyQt6: 
NumPy: 1.26.3
SciPy: 1.12.0
Dask: 2024.1.1
VisPy: 0.14.1
magicgui: 0.8.1
superqt: 0.6.1
in-n-out: 0.1.9
app-model: 0.2.4
npe2: 0.7.4

OpenGL:
- GL version: 2.1 Metal - 83.1
- MAX_TEXTURE_SIZE: 16384

Screens:
- screen 1: resolution 1680x1050, scale 2.0

Settings path:
- /Users/piotrsobolewski/Library/Application Support/napari/napari-dev_a1eb8b76ba95fa16ad06e26097b46b8455dfbf0b/settings.yaml

### 💡 Additional Context

Also occurs on 0.4.19
For Labels, Convert to Image is immediately functional without any re-selection.
For Images, Convert to Labels is immediately functional without any re-selection.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Just in case, I was able to reproduce this on Windows and seems like the problem comes from the layerlist context not getting updated when adding a new shape and so detecting the current selected shapes layer as empty (even when you already added some shapes) unless you change the current selection.

Also, seems like removing shapes doesn't properly update the layerlist context since then you can trigger the `Convert to Labels` action causing an error to raise (due to the layer being actually empty but that not being detected until a layer reselection is done):

![shapes_ctx_convert_label](https://github.com/napari/napari/assets/16781833/4c789d68-b638-4743-b0ee-abc73e0e4408)

Traceback:

<details>

```python-traceback
E:\Acer\Documentos\Quansight\Napari\napari\napari\layers\shapes\shapes.py:3087: RuntimeWarning: invalid value encountered in cast!
---------------------------------------------------------------------------
ValueError                                Traceback (most recent call last)
File ~\anaconda3\envs\napari-dev\lib\site-packages\app_model\backends\qt\_qaction.py:62, in QCommandAction._on_triggered(self=QMenuItemAction(MenuItem(when=None, group='1_con...tle=None, toggled=None), alt=None), app='napari'), checked=False)
     58 def _on_triggered(self, checked: bool) -> None:
     59     # execute_command returns a Future, for the sake of eventually being
     60     # asynchronous without breaking the API.  For now, we call result()
     61     # to raise any exceptions.
---> 62     self._app.commands.execute_command(self._command_id).result()
        self._command_id = 'napari:layer:convert_to_labels'
        self = QMenuItemAction(MenuItem(when=None, group='1_conversion', order=None, command=CommandRule(id='napari:layer:convert_to_labels', title='Convert to Labels', category=None, tooltip=None, status_tip=None, icon=None, enablement=Expr.parse('num_selected_image_layers >= 1 or num_selected_shapes_layers >= 1 and all_selected_layers_same_type and not selected_empty_shapes_layer'), short_title=None, toggled=None), alt=None), app='napari')
        self._app = Application('napari')

File ~\anaconda3\envs\napari-dev\lib\site-packages\app_model\registries\_commands_reg.py:206, in CommandsRegistry.execute_command(self=<CommandsRegistry at 0x23a64b93550 (120 commands)>, id='napari:layer:convert_to_labels', execute_asynchronously=False, *args=(), **kwargs={})
    202 except Exception as e:
    203     if self._raise_synchronous_exceptions:
    204         # note, the caller of this function can also achieve this by
    205         # calling `future.result()` on the returned future object.
--> 206         raise e
    207     future.set_exception(e)
    209 return future

File ~\anaconda3\envs\napari-dev\lib\site-packages\app_model\registries\_commands_reg.py:201, in CommandsRegistry.execute_command(self=<CommandsRegistry at 0x23a64b93550 (120 commands)>, id='napari:layer:convert_to_labels', execute_asynchronously=False, *args=(), **kwargs={})
    199 future: Future = Future()
    200 try:
--> 201     future.set_result(cmd(*args, **kwargs))
        future = <Future at 0x23a64bc4c10 state=pending>
        cmd = <function _convert_to_labels at 0x0000023A66371630>
        args = ()
        kwargs = {}
    202 except Exception as e:
    203     if self._raise_synchronous_exceptions:
    204         # note, the caller of this function can also achieve this by
    205         # calling `future.result()` on the returned future object.

File ~\anaconda3\envs\napari-dev\lib\site-packages\in_n_out\_store.py:890, in Store.inject_processors.<locals>._deco.<locals>._exec(*args=(), **kwargs={})
    888 @wraps(func)
    889 def _exec(*args: P.args, **kwargs: P.kwargs) -> R:
--> 890     result = func(*args, **kwargs)
        func = <function _convert_to_labels at 0x0000023A656DC1F0>
        args = ()
        kwargs = {}
    891     if result is not None:
    892         self.process(
    893             result,
    894             type_hint=type_hint,
    895             first_processor_only=first_processor_only,
    896             raise_exception=raise_exception,
    897         )

File ~\anaconda3\envs\napari-dev\lib\site-packages\in_n_out\_store.py:774, in Store.inject.<locals>._inner.<locals>._exec(*args=(), **kwargs={})
    772 # call the function with injected values
    773 try:
--> 774     result = func(**_kwargs)
        _kwargs = {'ll': []}
        func = <function _convert_to_labels at 0x0000023A629DACB0>
    775 except TypeError as e:
    776     # likely a required argument is still missing.
    777     # show what was injected and raise
    778     _argnames = (
    779         f"arguments: {set(_kwargs)!r}" if _kwargs else "NO arguments"
    780     )

File E:\Acer\Documentos\Quansight\Napari\napari\napari\layers\_layer_actions.py:75, in _convert_to_labels(ll=[])
     74 def _convert_to_labels(ll: LayerList):
---> 75     return _convert(ll, 'labels')
        ll = []

File E:\Acer\Documentos\Quansight\Napari\napari\napari\layers\_layer_actions.py:58, in _convert(ll=[], type_='labels')
     55 ll.pop(idx)
     57 if isinstance(lay, Shapes) and type_ == 'labels':
---> 58     data = lay.to_labels()
        lay = <Shapes layer 'Shapes' at 0x23a71c577f0>
     59 elif (
     60     not np.issubdtype(lay.data.dtype, np.integer) and type_ == 'labels'
     61 ):
     62     data = lay.data.astype(int)

File E:\Acer\Documentos\Quansight\Napari\napari\napari\layers\shapes\shapes.py:3088, in Shapes.to_labels(self=<Shapes layer 'Shapes'>, labels_shape=<class 'numpy.ndarray'> (2,) int32)
   3085     labels_shape = np.round(self._extent_data[1]) + 1
   3087 labels_shape = np.ceil(labels_shape).astype('int')
-> 3088 labels = self._data_view.to_labels(labels_shape=labels_shape)
        labels_shape = <class 'numpy.ndarray'> (2,) int32
        self._data_view = <napari.layers.shapes._shape_list.ShapeList object at 0x0000023A71CD7400>
        self = <Shapes layer 'Shapes' at 0x23a71c577f0>
   3090 return labels

File E:\Acer\Documentos\Quansight\Napari\napari\napari\layers\shapes\_shape_list.py:1275, in ShapeList.to_labels(self=<napari.layers.shapes._shape_list.ShapeList object>, labels_shape=<class 'numpy.ndarray'> (2,) int32, zoom_factor=1, offset=(0, 0))
   1272 if labels_shape is None:
   1273     labels_shape = self.displayed_vertices.max(axis=0).astype(int)
-> 1275 labels = np.zeros(labels_shape, dtype=int)
        labels_shape = <class 'numpy.ndarray'> (2,) int32
        np = <module 'numpy' from 'C:\\Users\\dalth\\anaconda3\\envs\\napari-dev\\lib\\site-packages\\numpy\\__init__.py'>
   1277 for ind in self._z_order[::-1]:
   1278     mask = self.shapes[ind].to_mask(
   1279         labels_shape, zoom_factor=zoom_factor, offset=offset
   1280     )

ValueError: negative dimensions are not allowed
```

</details>

So for some reason modifiying the layer data (adding or removing shapes) only gets acknowledged by the layerlist context when the layer selection changes 🤔?

### Comment 2 ([user]):

Yup, that's what I got in my debugging. 
This function:
https://github.com/napari/napari/blob/23110921d0f1ede34f927092d25ed9947fa25b68/napari/_app_model/context/_layerlist_context.py#L166-L167

Doesn't get called again when opening the contextual menu, only when layer selection changes, hence the two issues.
Should use state when right click is done. What I don't get is I tried to manually update context, but didn't have success.

I think the problem/solution lies here
https://github.com/napari/napari/blob/23110921d0f1ede34f927092d25ed9947fa25b68/napari/_qt/containers/_layer_delegate.py#L307-L318

To clarify, I was checking with `from napari._app_model.context import get_context`
So `get_context(viewer.layers)` before and after adding a shape gave me:
`'selected_empty_shapes_layer': True`

### Comment 3 ([user]):

So explicitly doing an update for the `selected_empty_shapes_layer` makes the action state (enabled/disabled) behave in the correct way. So, by doing something like this over the `show_context_menu`:

```python
    def show_context_menu(self, index, model, pos: QPoint, parent):
        """Show the layerlist context menu.
        To add a new item to the menu, update the _LAYER_ACTIONS dict.
        """
        if not hasattr(self, '_context_menu'):
            self._context_menu = build_qmodel_menu(
                MenuId.LAYERLIST_CONTEXT, parent=parent
            )

        layer_list: LayerList = model.sourceModel()._root
        ctx = get_context(layer_list)
        ctx.update(
            {
                "selected_empty_shapes_layer": _empty_shapes_layer_selected(
                    layer_list.selection
                )
            }
        )
        self._context_menu.update_from_context(ctx)
        self._context_menu.exec_(pos)
```

Checking, I think the context update is already being connected with to some of the layerlist events at https://github.com/napari/napari/blob/23110921d0f1ede34f927092d25ed9947fa25b68/napari/components/layerlist.py#L93-L108

Maybe there is another event that is not being connected there that could handle/detect when an item data changes? Or maybe a way to get the most up to date values/trigger keys recomputation from the context should be somehow implemented?

### Comment 4 ([user]):

Hmm, I don't like updating just that one thing when we make the menu -- what about the other conditions? We may have other bugs due to the lack of sync.
I think connecting to data change would be bad too, because 99% of the time the update would be useless--could cause performance issues?

What I've been trying to do is trigger that update manually, when the menu is opened, so when `show_context_menu` is called in the delegate.
I don't really get this app model stuff though 😢

### Comment 5 ([user]):

Following the idea to be able to trigger an update using the most updated selection values from the delegate, seems like adding to the `LayerListSelectionContextKeys` class definition a method to pass the selection which values want to be reflected over the context could help:

* At https://github.com/napari/napari/blob/4f4c063ae5dd79d6d188e201d44b8d57eba71909/napari/_app_model/context/_layerlist_context.py#L170 we could add to that class something like:

```python
    def update_by_selection(self, selection):
        """Update context with the given selection."""
        for k, get in self._getters.items():
            setattr(self, k, get(selection))
```

* Then the `LayerList` class definition at https://github.com/napari/napari/blob/4f4c063ae5dd79d6d188e201d44b8d57eba71909/napari/components/layerlist.py#L28 can have something like:

```python
    def selection_ctx_update(self):
        self._selection_ctx_keys.update_by_selection(self.selection)
```

* And then, from the layer delegate `show_context_menu` method at https://github.com/napari/napari/blob/4f4c063ae5dd79d6d188e201d44b8d57eba71909/napari/_qt/containers/_layer_delegate.py#L307 you could call this to be sure the layerlist selection context is actually up to date with the current layerlist selection:

```python
    def show_context_menu(self, index, model, pos: QPoint, parent):
        """Show the layerlist context menu.
        To add a new item to the menu, update the _LAYER_ACTIONS dict.
        """
        if not hasattr(self, '_context_menu'):
            self._context_menu = build_qmodel_menu(
                MenuId.LAYERLIST_CONTEXT, parent=parent
            )

        layer_list: LayerList = model.sourceModel()._root
        layer_list.selection_ctx_update()
        self._context_menu.update_from_context(get_context(layer_list))
        self._context_menu.exec_(pos)
```

Still not totally sure if there is a better approach/this a correct approach (my app-model knowledge is quite limited too 😅 ) but sharing the findings/possible fix I came up with. Here a branch if you want to give the code a more in context check: https://github.com/napari/napari/compare/main...dalthviz:napari:issue_6643

### Comment 6 ([user]):

Paging [user] Maybe you have some ideas how to attack this issue? It's a surprisingly easy one to hit in a normal workflow: open image, make shapes, annotate, try to convert -- greyed out.

### Comment 7 ([user]):

I'll take a look!

### Comment 8 ([user]):

Why do we use a dict with context instead of calculating it dynamically? 

https://github.com/pyapp-kit/app-model/blob/7f853e606daee0356cc6751e6a6e882c7179724e/src/app_model/expressions/_context.py#L151-L153

```python
def get_context(obj: object) -> Context | None:
    """Return context for any object, if found."""
    return _OBJ_TO_CONTEXT.get(id(obj))
```

This is an error-prone approach. It is easy to forget connect any event.

### Comment 9 ([user]):

Not sure I follow [user] but using `get_context` does not result in updated keys.
If I make an empty Shapes:
```python
from napari._app_model.context import get_context

get_context(viewer.layers)
Out[2]: Context({'num_selected_layers': 1, 'num_selected_layers_linked': False, 'num_unselected_linked_layers': 0, 'active_layer_is_rgb': False, 'active_layer_type': 'shapes', 'num_selected_image_layers': 0, 'num_selected_labels_layers': 0, 'num_selected_points_layers': 0, 'num_selected_shapes_layers': 1, 'num_selected_surface_layers': 0, 'num_selected_vectors_layers': 0, 'num_selected_tracks_layers': 0, 'active_layer_ndim': None, 'active_layer_shape': None, 'active_layer_is_image_3d': False, 'active_layer_dtype': None, 'all_selected_layers_same_shape': True, 'all_selected_layers_same_type': True, 'all_selected_layers_labels': False, 'selected_empty_shapes_layer': True}, {'num_layers': 1}, {}, SettingsAwareContext({}))
```
But then when I draw a Shape and run it again:
```python
get_context(viewer.layers)
Out[3]: Context({'num_selected_layers': 1, 'num_selected_layers_linked': False, 'num_unselected_linked_layers': 0, 'active_layer_is_rgb': False, 'active_layer_type': 'shapes', 'num_selected_image_layers': 0, 'num_selected_labels_layers': 0, 'num_selected_points_layers': 0, 'num_selected_shapes_layers': 1, 'num_selected_surface_layers': 0, 'num_selected_vectors_layers': 0, 'num_selected_tracks_layers': 0, 'active_layer_ndim': None, 'active_layer_shape': None, 'active_layer_is_image_3d': False, 'active_layer_dtype': None, 'all_selected_layers_same_shape': True, 'all_selected_layers_same_type': True, 'all_selected_layers_labels': False, 'selected_empty_shapes_layer': True}, {'num_layers': 1}, {}, SettingsAwareContext({}))
```
Still see `'selected_empty_shapes_layer': True` maybe there is some caching?

### Comment 10 ([user]):

> Not sure I follow [user] but using `get_context` does not result in updated keys.

Yes, because `get_context` is returning some value from cache, instead of calculating them. 

So it is simple to forget about connecting some event, and you end with the wrong cached state.

## PR Review Comments

**[user]** on `napari/components/layerlist.py`:

I need to find a better place to do this, but now I put it here to show usage.

**[user]** on `napari/components/layerlist.py`:

What about in `_QtMainWindow` like in #6915 ?

I thought that these 'misc' type context keys would ideally go in `NapariApplication` but this is outside of Qt.

**[user]** on `napari/components/layerlist.py`:

moved to `qt_layer_list`

**[user]** on `napari/components/layerlist.py`:

I'm not as familiar here, but I would have thought this context key wouldn't fit with qt layerlist, considering the other layerlist type context keys being so tied to layerlist, e.g., number of layers etc. But as you wish.

**[user]** on `napari/components/layerlist.py`:

But this context requires qt to work.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
