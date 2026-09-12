# GH1154_matplotlib_30795: Fix array alpha to multiply (not replace) existing RGBA alpha — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/matplotlib/matplotlib/issues/26092
- Repo: https://github.com/matplotlib/matplotlib

## Issue Description

### Bug summary

Hi,
Whereas `alpha = constant` works with RGB image, this is not the case when working with an `array-type` for alpha.
(In my real case, I can only pass standard imshow parameters like `alpha `to the function of the library I use, and not a RGBA array).
Patrick

### Code for reproduction

```python
import numpy as np
import matplotlib.pyplot as plt
from skimage.color import gray2rgb

arr = np.random.random((10, 10))
arr_rgb = gray2rgb(arr)

alpha = np.ones_like(arr)
alpha[:5] = 0.2

plt.figure()
plt.tight_layout()
plt.subplot(121)
plt.title("Expected outcome")
plt.imshow(arr, alpha=alpha, cmap='gray')
plt.subplot(122)
plt.title("Actual outcome")
plt.imshow(arr_rgb, alpha=alpha)
plt.show()
```


### Actual outcome

![image](https://github.com/matplotlib/matplotlib/assets/16154687/89322c0b-4ccd-46e1-9f2a-50b5f3511dfa)


### Expected outcome

![image](https://github.com/matplotlib/matplotlib/assets/16154687/4d7fcedf-2c54-4f07-a35d-ad23afeb9df6)


### Additional information

_No response_

### Operating system

Windows

### Matplotlib Version

3.7.1

### Matplotlib Backend

TkAgg

### Python version

Python 3.10.11

### Jupyter version

_No response_

### Installation

pip

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Here is an example without `skimage` (fixed by #28437):

```python
import numpy as np
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

arr = np.random.random((10, 10))
cmap = plt.get_cmap('gray')
norm = mcolors.Normalize()
arr_rgb = cmap(norm(arr))[:, :, :3]

alpha = np.ones_like(arr)
alpha[:5] = 0.2

plt.subplot(121)
plt.title("Expected outcome")
plt.imshow(arr, alpha=alpha, cmap='gray')

plt.subplot(122)
plt.title("Actual outcome")
plt.imshow(arr_rgb, alpha=alpha)

plt.show()
```

I get this with both v3.7.1 and `main`:
![test](https://github.com/matplotlib/matplotlib/assets/10599679/c4b8fd13-dd4e-48d6-90fb-390a0cf0d8f5)

The [docstring for `imshow`](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.imshow.html#matplotlib.axes.Axes.imshow) does suggest that _alpha_ may be an array, but it also says the array should be the same shape as the image so I assume that only means for the (M, N) case.  So I'm not sure whether this is a bug or a documentation issue.  ETA: though I'm not sure why the current behaviour would be desired - if you didn't want _alpha_ to have an effect then you would just not pass it.

### Comment 2 ([user]):

hello [user],
Thanks for replying.
The library I use (Orix) manipulates complex object and allows to plot data thanks to this function : [`plot_map()`](https://orix.readthedocs.io/en/latest/reference/generated/orix.plot.CrystalMapPlot.plot_map.html)
The plotting is based on a RGB array (issue from a complex object) and I wish to pass `alpha` to highlight some area of my map. I can't act directly on the RGB array.
Patrick

### Comment 3 ([user]):

This is a bug.  `imshow` basically has two orthogonal code paths, one for if the user passes us a ndim==2 array (which goes through color mapping) and one for for if eth user passes us a ndim==3 array (which more-or-less just goes out).

I suspect that when we implemented the "alapha-as-array" we forgot about the RGB(A) case.

### Comment 4 ([user]):

Yeah, the issue is in https://github.com/matplotlib/matplotlib/blob/dbc906abe5b8a8a5667f81a305e042e7e98c13e9/lib/matplotlib/image.py#L553-L576 where we do apply alpha, but are asking for the scalar alpha not the array alpha.

(withheld: the upstream fix is not part of the task) is where this feature came in and where we picked up the explicit call to `_get_scalar_alpha`.


That said, I think the fix is to add logic to https://github.com/matplotlib/matplotlib/blob/dbc906abe5b8a8a5667f81a305e042e7e98c13e9/lib/matplotlib/image.py#L557-L558 where we promote RGB -> RGBA to take into account a possibly array-like alpha.

I suspect that we have the same bug in https://github.com/matplotlib/matplotlib/blob/dbc906abe5b8a8a5667f81a305e042e7e98c13e9/lib/matplotlib/image.py#L580 which is handling the fully un-sampled case and have confirmed we see the same bug in https://github.com/matplotlib/matplotlib/blob/dbc906abe5b8a8a5667f81a305e042e7e98c13e9/lib/matplotlib/image.py#L554-L556 


I am going to label this as good first issue as it is a clear bug (array alpha should work with  RGB input).  I would say this is a medium difficulty because the image processing code is a bit complicated. Most of that complexity is there for a good reason so be prepared to understand a majority of the `_make_image` function., The only dicey thing to work out is what to do in the case of the user passing both and RGBA array _and_ an array alpha:  Do we error, discard one (and warn), or blend them?

The patch:

> _Reference patch removed from the agent-visible spec. It lives in `reference/` and is readable by the grader only._

fixes at least the obvious cases, but does not address the "what about RGBA" issue and I think will double apply the alpha in scalar cases.

I don't have time today to chase through those details or write tests.

### Comment 5 ([user]):

### Good first issue - notes for new contributors

This issue is suited to new contributors because it does not require understanding of the Matplotlib internals. To get started, please see our [contributing guide](https://matplotlib.org/stable/devel/index).

**We do not assign issues**. Check the *Development* section in the sidebar for linked pull requests (PRs). If there are none, feel free to start working on it. If there is an open PR, please collaborate on the work by reviewing it rather than duplicating it in a competing PR.

If something is unclear, please reach out on any of our [communication channels](https://matplotlib.org/stable/devel/contributing.html#get-connected).

### Comment 6 ([user]):

> The only dicey thing to work out is what to do in the case of the user passing both and RGBA array and an array alpha: Do we error, discard one (and warn), or blend them?

Looks like we have a precedent that _alpha_ overrides the existing alpha channel on an rgba tuple.

https://github.com/matplotlib/matplotlib/blob/72885cc1ebd458d1b197a43daaaacbfaebbe597e/lib/matplotlib/colors.py#L400-L401

Edit: OTOH we also have precedent for ignoring _alpha_.
https://matplotlib.org/stable/api/cm_api.html#matplotlib.cm.ScalarMappable.to_rgba

### Comment 7 ([user]):

Oh the fun, there is also a precedent that it doesn't for ScalarMappables too :)
https://github.com/matplotlib/matplotlib/blob/72885cc1ebd458d1b197a43daaaacbfaebbe597e/lib/matplotlib/cm.py#L454-L457

### Comment 8 ([user]):

And via https://github.com/matplotlib/matplotlib/blob/3b30f47d83c8bc8a2d4de4d8e234f2eeada41b88/lib/matplotlib/image.py#L560-L564  if you pass an RGBA array and a scalar alpha they get combined so we have precedent for 3 of the 4 options!

```python
import numpy as np
import matplotlib.pyplot as plt
a = np.zeros([2, 2, 4])
a[:, :, 0] = 1
a[:, :, 3] = np.linspace(0, 1, 4).reshape(2, 2)
fig, (ax1, ax2) = plt.subplots(1, 2)
ax1.imshow(a)
ax2.imshow(a, alpha=.5)
plt.show()
```

### Comment 9 ([user]):

So we should add one that raises, to complete the set 🤪

More seriously, I think it’s probably more important for `imshow` to be consistent with itself than consistent with other things, in which case it should also blend for  array alpha.  (Though I have not followed exactly what that `_resample` function does so I don’t know how difficult it would be.)

### Comment 10 ([user]):

Hello there! I'd like to contribute to this issue. I'm new to contributing to Matplotlib, so please pardon me if I ask any silly questions! I'd just like to clarify what the issue is, and the general sketch of the solution:

When displaying images using Matplotlib, if the provided image is of 2 dimensions (grayscale image) and an `alpha` parameter is provided, the image is plotted with the given `alpha` parameter being used to make certain pixels of the image opaque by a factor: if a scalar value of `alpha` is provided, the entire image is affected. If an array is provided for `alpha`, then each pixel of the image is affected by the corresponding value in the `alpha` array.

However, if the provided image is of 3 dimensions (RGB image) and an array is provided for `alpha`, the image isn't affected in any way. If a scalar value is provided, the entire image is affected as is what happened in the last case.

If the provided image is of 4 dimensions (RGBA), and a value for alpha is provided, no matter what the value is (scalar or array), the image isn't affected: it uses the preexisting alpha array present in the image.

We'd like to change this behavior: the case for grayscale images works well, so we don't need to change that. For cases where the dimensions of the image are > 2, we'd like to add cases covering all bases: if the image is RGB, add cases where the display function can accept array values for alpha, and if the image is RGBA, decide on a way to let the user know that there are two alpha values: one already provided in the image, and one provided by them. 

The way to start would be by examining the code snippets @/tacaswell listed, and making the corresponding changes.

Please pardon me if I've made any mistake in my clarification! Thanks for patiently reading through this.

## PR Review Comments

**[user]** on `doc/api/next_api_changes/behavior/28437-CH.rst`:

This is not quite right - for RGBA the _alpha_ parameter replaced the image alpha channel.  So _alpha_ was not ignored.

**[user]** on `doc/api/next_api_changes/behavior/28437-CH.rst`:

The issue here is that [user] edited the API-change note for an old PR (#28437) instead of creating a new note, which is why it is misleading.

**[user]** on `doc/api/next_api_changes/behavior/28437-CH.rst`:

Ah OK.  So this is actually correct relative to v3.10.0.  Does that mean that this is what we want for the v3.11.0 release notes and therefore this is good to go (after a rebase)?  Or should v3.11.0 release notes mention that this changed already at v3.10.1 and we're changing it again?

**[user]** on `doc/api/next_api_changes/behavior/28437-CH.rst`:

Or should the release note just describe the change relative to current (v3.10.8) behaviour?  I went looking for examples and found that the [v3.9.1 change](https://matplotlib.org/stable/api/prev_api_changes/api_changes_3.9.1.html) also appears in the [v3.10.0 notes](https://matplotlib.org/stable/api/prev_api_changes/api_changes_3.10.0.html#documentation-specific-custom-sphinx-roles-are-now-semi-public), but the [v3.9.2 change](https://matplotlib.org/stable/api/prev_api_changes/api_changes_3.9.2.html) does not.

So we do not have an obvious pattern for whether changes from micro releases get mentioned in the next meso release notes.  I think probably the least confusing for the user would be to spell out that this has changed twice.  I will push something to that effect tomorrow unless someone says otherwise or beats me to it.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
