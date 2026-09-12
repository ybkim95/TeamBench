# GH1085_matplotlib_31313: Fixed lingering bugs with image rendering related to exact half display pixels — Full Specification (Planner Only)

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
<!-- Please describe the pull request, using the questions below as guidance, and link to any relevant issues and PRs:

- Why is this change necessary?
- What problem does it solve?
- What is the reasoning for this implementation?

Additionally, please summarize the changes in the title, for example "Raise ValueError on
non-numeric input to set_xlim" and avoid non-descriptive titles such as "Addresses
issue #8576".

If possible, please provide a minimum self-contained example.
-->
This is a follow-on to #31021 to fix image-rendering bugs when a display pixel is exactly aligned with the edge between two image pixels (or with the edge of the image).  An attempt at a fix was part of #31021, but the tests there had not been carefully crafted to verify that the bugs were comprehensively fixed.

### Before this PR
<img width="1000" height="500" alt="before" src="https://github.com/user-attachments/assets/735c8299-f86e-47c3-8e33-8235919ea97e" />

### After this PR
<img width="1000" height="500" alt="after" src="https://github.com/user-attachments/assets/76603a9a-1e56-429a-917d-81638cef8207" />

### Generating code
```python
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.transforms import Transform

# Create a nonaffine identity to easily convert an affine transform to its nonaffine equivalent
class NonAffineIdentityTransform(Transform):
    input_dims = 2
    output_dims = 2

    def inverted(self):
        return self
nonaffine_identity = NonAffineIdentityTransform()

fig = plt.figure(figsize=(10, 5))
fig.set_facecolor('g')

# All values in this test are chosen carefully so that many display pixels are
# aligned with an edge or a corner of an input pixel

# Layout:
# Top row is origin='upper', bottom row is origin='lower'
# Column 1: affine transform, anchored at whole pixel
# Column 2: affine transform, anchored at half pixel
# Column 3: nonaffine transform, anchored at whole pixel
# Column 4: nonaffine transform, anchored at half pixel
# Column 5: affine transform, anchored at half pixel, interpolation='hanning'

# Each axes patch is magenta, so seeing a magenta line at an edge of the image
# means that the image is not filling the axes

corner_x = [0.01, 0.199, 0.41, 0.599, 0.81]
corner_y = [0.1, 0.5]

axs = []
for cy in corner_y:
    for ix, cx in enumerate(corner_x):
        mx = cx + 0.0005 if ix in [1, 3, 4] else cx
        my = cy + 0.011 if ix in [1, 3, 4] else cy
        axs.append(fig.add_axes([mx, my, 0.175, 0.35], xticks=[], yticks=[]))

N = 10

data = np.arange(N**2).reshape((N, N)) % 9
seps = np.arange(-0.5, N)

for i, ax in enumerate(axs):
    ax.set_facecolor('m')

    ax.imshow(data, cmap='Blues',
              interpolation='hanning' if i % 5 == 4 else 'nearest',
              origin='upper' if i >= 5 else 'lower',
              transform=nonaffine_identity + ax.transData if i % 4 >= 2 else ax.transData)

    ax.vlines(seps, -0.5, N - 0.5, linewidth=0.5, color='red', linestyle=(0, (3, 6)))
    ax.hlines(seps, -0.5, N - 0.5, linewidth=0.5, color='red', linestyle=(0, (3, 6)))

    for spine in ax.spines:
        ax.spines[spine].set_linestyle((0, (5, 10)))

plt.show()
```

## AI Disclosure
<!-- If you used AI in writing this PR, please briefly describe how.
Read our policy at
https://matplotlib.org/devdocs/devel/contribute.html#restrictions-on-generative-ai-usage
-->
N/A

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

**[user]** on `lib/matplotlib/tests/test_image.py`:

I'm not sure how exactly (maybe checking `ax.get_window_extent()`?), but if this test is very dependent on specific locations of Axes, then it might be a good idea to assert that they are in the places you expect, in case layout somehow changes in the future?

Or, if possible, maybe switch to figure-level artists, to remove some level of indirection (but I'm not sure if those exercise what you want)?

**[user]** on `lib/matplotlib/tests/test_image.py`:

Rather than testing specific values, I added asserts for the precise height/width for each axes and the precise anchoring (whether on whole pixels or half pixels), which are the critical requirements.  Translations, if they were to happen for some reason, would be "okay" as far as this test is concerned.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
