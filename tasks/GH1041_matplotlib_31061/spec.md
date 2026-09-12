# GH1041_matplotlib_31061: BUG: Fix text appearing far outside valid axis scale range — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/matplotlib/matplotlib

## PR Description

## PR summary
Closes https://github.com/matplotlib/matplotlib/issues/31054

`Text` didn't have a `get_tightbbox` override yet, so this adds that with some handling for no-show cases. The `_in_axes_domain` check is not exclusive to text and may be useful elsewhere, so was given to `Artist` more broadly.

The plot in the original issue renders correctly now, and I can confirm it was broken for me before:

```python
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x) * 10

fig, ax = plt.subplots()
ax.plot(x, y)
ax.set_yscale('log')
ax.text(5, -5, "I am at y = -5", color='red')

plt.savefig("test_gh31054.png", bbox_inches='tight')
```

<img width="558" height="413" alt="test_gh31054" src="https://github.com/user-attachments/assets/0b496245-22be-4d8b-9fc5-247ebb380190" />


## PR checklist
<!-- Please mark any checkboxes that do not apply to this PR as [N/A].-->

- [x] "closes #0000" is in the body of the PR description to [link the related issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue)
- [x] new and changed code is [tested](https://matplotlib.org/devdocs/devel/testing.html)
- [n/a] *Plotting related* features are demonstrated in an [example](https://matplotlib.org/devdocs/devel/document.html#write-examples-and-tutorials)
- [n/a] *New Features* and *API Changes* are noted with a [directive and release note](https://matplotlib.org/devdocs/devel/api_changes.html#announce-changes-deprecations-and-new-features)
- [n/a] Documentation complies with [general](https://matplotlib.org/devdocs/devel/document.html#write-rest-pages) and [docstring](https://matplotlib.org/devdocs/devel/document.html#write-docstrings) guidelines

## PR Review Comments

**[user]** on `lib/matplotlib/text.py`:

```python
        if not self.get_visible() or self.get_text() == "":
            return Bbox.null()
```

I had originally included these lines, but they were changing a half dozen baseline images as plots expanded to fill space where there was empty/invisible text. Removed for now, but I think that's probably the right behavior and we can discuss including it.

**[user]** on `lib/matplotlib/artist.py`:

Should we negate the logic to `_outside_axes_domain`?

> Returns True if the artist is in an Axes (i.e. self.axes is set) but outside the data range.

**[user]** on `lib/matplotlib/artist.py`:

Sure, that better reflects how we're using it. Updated

**[user]** on `lib/matplotlib/text.py`:

If you think that might be important, you can target that change to the `text-overhaul` branch.

**[user]** on `lib/matplotlib/text.py`:

Do you mean this PR or just that change?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
