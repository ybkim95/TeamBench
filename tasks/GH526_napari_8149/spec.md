# GH526_napari_8149: Ensure contrast limits are computed on original dtype with projected thick slices — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/napari/napari/issues/8148
- Repo: https://github.com/napari/napari

## Issue Description

### 🐛 Bug Report

Opening astronaut:

<img width="1277" height="1011" alt="Image" src="https://github.com/user-attachments/assets/fa3d4743-911d-4883-99ac-2461c6bea2db" />

### 💡 Steps to Reproduce

1. Open the sample Astronaut

### 💡 Expected Behavior

The thumbnail should look like the image layer data?

### 🌎 Environment

napari: 0.6.2rc1.dev71+g0294fad15
Platform: macOS-14.5-arm64-arm-64bit-Mach-O
System: MacOS 14.5
Python: 3.13.3 | packaged by conda-forge | (main, Apr 14 2025, 20:44:30) [Clang 18.1.8 ]
Qt: 6.9.0
PyQt6: 6.9.0
NumPy: 2.2.6
SciPy: 1.15.3
Dask: 2025.5.1
VisPy: 0.15.2
magicgui: 0.10.0
superqt: 0.7.3
in-n-out: 0.2.1
app-model: 0.3.1
psygnal: 0.13.0
npe2: 0.7.9
pydantic: 2.11.5

OpenGL:
- PyOpenGL: 3.1.9
- GL version: 2.1 Metal - 88.1
- MAX_TEXTURE_SIZE: 16384
- GL_MAX_3D_TEXTURE_SIZE: 2048

Screens:
- screen 1: resolution 1680x1050, scale 2.0

Optional:
- numba: 0.61.2
- triangle: 20250106
- napari-plugin-manager: 0.1.6
- bermuda: 0.1.4
- PartSegCore not installed

Experimental Settings:
- Async: False
- Autoswap buffers: False
- Triangulation backend: Fastest available

Settings path:
- /Users/piotrsobolewski/Library/Application Support/napari/napari-dev_a1eb8b76ba95fa16ad06e26097b46b8455dfbf0b/settings.yaml

Launch command:
- /Users/piotrsobolewski/Dev/miniforge3/envs/napari-dev/bin/napari

Plugins:
- napari-animation: 0.0.8 (2 contributions)
- napari-skimage: 0.5.0 (64 contributions)
- napari: 0.6.2.dev11+g6371fffe9 (86 contributions)
- napari-tiff: 0.1.5.dev1+gebf2362 (2 contributions)
- napari-svg: 0.2.1 (2 contributions)
- napari-console: 0.1.3 (0 contributions)

### 💡 Additional Context

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I tested a number of samples, looks like just RGB images are messed up in the thumbnail.

### Comment 2 ([user]):

Bisect points to fe7645131317d266bb8f316fc85cebec61abb6d4
cc: [user]

### Comment 3 ([user]):

Yep, happens due to projection mode again. Setting to none fixes it. 
I was wondering during initial implementation, and again now, if we should just add a guard that if there is no slick slice we just don't do any calculation. Although, as [user] said in theory a thickness of zero shouldn't change the visualization of anything.

<img width="403" height="244" alt="Image" src="https://github.com/user-attachments/assets/cf4f0f30-d14a-4fa0-83a7-9966b45a669f" />

### Comment 4 ([user]):

Well if anything setting the default to `mean` is helping us find a bunch of bugs 😅  I'm looking into it.

## PR Review Comments

**[user]** on `src/napari/layers/image/_image_utils.py`:

Why do we need to specify `copy=False`

**[user]** on `src/napari/layers/image/_image_utils.py`:

Because we don't need to create a copy if it's not necessary.

**[user]** on `src/napari/layers/image/_image_utils.py`:

Ok. So `np.sum`, `np.mean` accept the `dtype` argument, but the `np.max` and `np.min` do not. 

So we cannot just use 
```python
return func(data, tuple(axis), dtype=data.dtype)
```

but all functions accept `out` to provide a target array that also specifies out dtype. 

So we may wrote 
```python
out = np.empty(target_shape, dtype=data.dtype)
return func(data, tuple(axis), out=out)
```

Or just change 

```python
    if mode == ImageProjectionMode.SUM:
        func = np.sum
    elif mode == ImageProjectionMode.MEAN:
        func = np.mean
    elif mode == ImageProjectionMode.MAX:
        func = np.max
    elif mode == ImageProjectionMode.MIN:
        func = np.min
```

to

```python
    if mode == ImageProjectionMode.SUM:
        func = np.sum
    elif mode == ImageProjectionMode.MEAN:
        func = partial(np.mean, dtype=data.dtype)
    elif mode == ImageProjectionMode.MAX:
        func = np.max
    elif mode == ImageProjectionMode.MIN:
        func = np.min
```

Did I'm correct? 

Both will remove additional array allocation.

**[user]** on `src/napari/layers/image/_image_utils.py`:

Sure but is there any reason to do this over my fix? I think mine looks more intuitive, but I don't really care much.

**[user]** on `src/napari/layers/image/_image_utils.py`:

because both options remove additional data allocation when using `mean` mode?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
