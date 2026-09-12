# GH1067_matplotlib_30054: Fixed an off-by-half-pixel bug in image resampling when using a nonaffine transform (e.g., a log axis) — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/matplotlib/matplotlib

## PR Description

<!--
Thank you so much for your PR!  To help us review your contribution, please check
out the development guide https://matplotlib.org/devdocs/devel/index.html
-->

## PR summary
This PR fixes a off-by-half-pixel bug in `matplotlib._image.resample()` when using a nonaffine transform.  (This function is used internally when drawing an image artist.)  The mesh for nonaffine transforms is mistakenly computed at the lower corners of pixels instead of the centers of pixels, which results in a half-pixel shift in the output.  Here are illustrative plots and the generating script.

Before this PR:
![download (16)](https://github.com/user-attachments/assets/4e0b072d-1d54-4cc6-91a3-e5e7f212b565)

After this PR:
![Figure_1](https://github.com/user-attachments/assets/204e5bb5-b71b-4617-bcfc-c60f54f7fad2)

Script:
```python
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.transforms import Affine2D, Transform
from matplotlib.image import resample, NEAREST, BILINEAR

in_data = np.array([[0.1, 0.3, 0.2]])
in_shape = in_data.shape
in_edges = np.arange(in_shape[1] + 1)

out_shape = (1, 10)
out_edges = np.arange(out_shape[1] + 1)
affine_data = np.empty(out_shape)
nonaffine_data = np.empty(out_shape)

# Create a simple affine transform for scaling the input array
affine = Affine2D().scale(sx=out_shape[1] / in_shape[1], sy=1)

# Create a nonaffine version of the same transform by compositing with a nonaffine identity transform
class NonAffineIdentityTransform(Transform):
    input_dims = 2
    output_dims = 2

    def inverted(self):
        return self
nonaffine = NonAffineIdentityTransform() + affine

fig, axs = plt.subplots(3, 1, figsize=(4.8, 6.4), layout="constrained")

axs[0].stairs(in_data[0, :], in_edges)
axs[0].grid(ls='dotted')
axs[0].set_xticks(in_edges)
axs[0].set_title('Original data')

resample(in_data, affine_data, affine, interpolation=NEAREST)
resample(in_data, nonaffine_data, nonaffine, interpolation=NEAREST)

axs[1].stairs(affine_data[0, :], out_edges, label='affine')
axs[1].stairs(nonaffine_data[0, :], out_edges, ls='dashed', label='nonaffine')
axs[1].grid(ls='dotted')
axs[1].set_xticks(out_edges)
axs[1].legend()
axs[1].set_title('Nearest-neighbor resampling')

resample(in_data, affine_data, affine, interpolation=BILINEAR)
resample(in_data, nonaffine_data, nonaffine, interpolation=BILINEAR)

axs[2].stairs(affine_data[0, :], out_edges, label='affine')
axs[2].stairs(nonaffine_data[0, :], out_edges, ls='dashed', label='nonaffine')
axs[2].grid(ls='dotted')
axs[2].set_xticks(out_edges)
axs[2].legend()
axs[2].set_title('Linear resampling')

plt.show()
```

## PR checklist
<!-- Please mark any checkboxes that do not apply to this PR as [N/A].-->

- [N/A] "closes #0000" is in the body of the PR description to [link the related issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue)
- [x] new and changed code is [tested](https://matplotlib.org/devdocs/devel/testing.html)
- [N/A] *Plotting related* features are demonstrated in an [example](https://matplotlib.org/devdocs/devel/document.html#write-examples-and-tutorials)
- [N/A] *New Features* and *API Changes* are noted with a [directive and release note](https://matplotlib.org/devdocs/devel/api_changes.html#announce-changes-deprecations-and-new-features)
- [N/A] Documentation complies with [general](https://matplotlib.org/devdocs/devel/document.html#write-rest-pages) and [docstring](https://matplotlib.org/devdocs/devel/document.html#write-docstrings) guidelines

<!--We understand that PRs can sometimes be overwhelming, especially as the
reviews start coming in.  Please let us know if the reviews are unclear or
the recommended next step seems overly demanding, if you would like help in
addressing a reviewer's comments, or if you have been waiting too long to hear
back on your PR.-->

## PR Review Comments

**[user]** on `src/_image_wrapper.cpp`:

Could you leave a comment explaining what's happening and why the half pixel offset is needed?

**[user]** on `src/_image_wrapper.cpp`:

I added a comment that is hopefully helpful

**[user]** on `lib/matplotlib/tests/test_image.py`:

```suggestion
    [(np.array([[0.1, 0.3, 0.2]]), mimage.NEAREST,
      np.array([[0.1, 0.1, 0.1, 0.3, 0.3, 0.3, 0.3, 0.2, 0.2, 0.2]])),
     (np.array([[0.1, 0.3, 0.2]]), mimage.BILINEAR,
```

These values are implemented in a private namespace, but are available in a public namespace (which is already imported directly)

This should also resolve the type hint problems

**[user]** on `src/_image_wrapper.cpp`:

That helps, thanks!

**[user]** on `lib/matplotlib/tests/test_image.py`:

```suggestion
    mimage.resample(data, affine_result, affine_transform, interpolation=interpolation)
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
