# GH463_napari_8772: Fix: Fire world unit updates after removing layer — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/napari/napari/issues/8771
- Repo: https://github.com/napari/napari

## Issue Description

### 🐛 Bug Report

Removing a layer that results in the viewer having inconsistent units across layers does not restore the unit-aware rendering of the remaining layers that are consistent.

### 💡 Steps to Reproduce

run this script then remove the points layer
```python
import napari
from skimage import data

cells3d = data.cells3d()
membrane = cells3d[:, 0, :, :]
nuclei = cells3d[:, 1, :, :]

viewer = napari.Viewer()

viewer.add_image(
    membrane,
    colormap='magenta',
    scale = (0.1, 0.1, 0.1),
    units = ('micrometer','micrometer','micrometer')
)
viewer.add_image(
    nuclei,
    colormap='green',
    blending='additive',
    scale = (100, 100, 100),
    units = ('nanometer','nanometer','nanometer')
)
viewer.add_labels(
    nuclei > 0,
    blending='additive'
)

napari.run()
```

### 💡 Expected Behavior

_No response_

### 🌎 Environment

napari: 0.7.0rc0
Platform: Windows-11-10.0.26200-SP0
Python: 3.13.11 (main, Dec 9 2025, 19:02:08) [MSC v.1944 64 bit (AMD64)]
Qt: 6.10.0
PyQt6: 6.10.2
NumPy: 2.2.6
SciPy: 1.17.0
Dask: 2026.1.1
VisPy: 0.16.1
magicgui: 0.10.1
superqt: 0.7.8
in-n-out: 0.2.1
app-model: 0.5.1
psygnal: 0.15.1
npe2: 0.8.1
pydantic: 2.12.5

OpenGL:
- PyOpenGL: 3.1.10
- GL version: 4.6.0 NVIDIA 581.08
- MAX_TEXTURE_SIZE: np.int32(32768)
- GL_MAX_3D_TEXTURE_SIZE: 16384

Screens:
- screen 1: resolution 2560x1440, scale 1.5
- screen 2: resolution 1440x2560, scale 1.0

Optional:
- numba not installed
- triangle not installed
- napari-plugin-manager: 0.1.10
- bermuda not installed
- PartSegCore not installed

Experimental Settings:
- Async: False
- Autoswap buffers: False
- Triangulation backend: Fastest available

Settings path:
- C:\Users\timmo\AppData\Local\napari\.venv_7154e37be9702ac832ac8d7cb7028f2981aa8fa3\settings.yaml

Launch command:
- testing.py

Plugins:
- napari: 0.5.6 (88 contributions)
- napari-console: 0.1.4 (0 contributions)
- napari-metadata: 0.2.0a1.dev8+g8b2bfd3d6 (2 contributions)
- napari-svg: 0.2.1 (2 contributions)
- nbatch: 0.0.4 (0 contributions)
- ndevio: 0.9.0 (18 contributions)
- ndev-settings: 0.4.1 (2 contributions)
- ndev-themes: 0.1.1 (1 contributions)
- ome-types: 0.6.3 (2 contributions)

### 💡 Additional Context

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

BTW I made this issue while trying to reproduce the axes overlay missing like I reported here: [#release > 0.7.0 @ 💬](https://napari.zulipchat.com/#narrow/channel/215289-release/topic/0.2E7.2E0/near/579365359)
I am unable to reproduce. 
However #8772 does refire unit rendering updates, and if the axes overlay was locked into inconsistent rendering maybe this is a fix. Will keep playing.

## PR Review Comments

**[user]** on `src/napari/components/layerlist.py`:

This makes sense to me, but shouldn't we only fire the event if the value changed?

**[user]** on `src/napari/_qt/qt_viewer.py`:

Maybe so we don't reach down into canvas private api, we can just do `self.viewer.layers.events.units()`?

**[user]** on `src/napari/_qt/qt_viewer.py`:

If I try that, the qt_viewer test I made fails (but maybe its a bad test?).Because `self.viewer.layers.events.units()` seems connected to `_deferred_world_units_update` I think its not working because we need `on_draw()` to fire in that case. But, I would think that using the private method would be more performant because it doesn't have to what for the draw in order to then trigger a new draw.

**[user]** on `src/napari/components/layerlist.py`:

Hmmm, this is potentially a good idea. Would it make sense to then put them in the `insert` and `__delitem__` methods?
If I try that it seems like I need a hasattr check for the existence of `events.units`, but then the canvas method is not needed in qt_viewer (because we don't rely on the layerlist events but rather the actual insertion)

**[user]** on `src/napari/_qt/qt_viewer.py`:

This to me points to the fact that this whole thing of units shouldn't be a thing on the canvas... But I guess for now this is ok :shrug:

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
