# GH1135_matplotlib_31278: Fix `clabel` manual argument not accepting unit-typed coordinates — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/matplotlib/matplotlib/issues/27525
- Repo: https://github.com/matplotlib/matplotlib

## Issue Description

### Bug summary

As found in #27490, while `contour` does appear to allow units, if you pass manual label locations to the `manual` argument of `clabel, it will fail.

### Code for reproduction

```python
import datetime

import numpy as np
import matplotlib.pyplot as plt


# Sample data for contour plot
dates = [datetime.datetime(2023, 10, 1) + datetime.timedelta(days=i) for i in range(10)]
x_start, x_end, x_step = -10.0, 5.0, 0.5
y_start, y_end, y_step = 0, 10, 1

x = np.arange(x_start, x_end, x_step)
y = np.arange(y_start, y_end, y_step)

# In this case, Y axis has dates
X, Y = np.meshgrid(x, dates)

rows = len(X)
cols = len(X[0])

z1D = np.arange(rows * cols)
Z = z1D.reshape((rows, cols))

fig, ax = plt.subplots()
CS = ax.contour(X, Y, Z)

ax.clabel(CS, CS.levels, inline=True, fmt=dict(zip(CS.levels, dates)),
          manual=[(x, y) for x, y in zip(x, dates)])
```


### Actual outcome
```python
Traceback (most recent call last):
  File "/home/elliott/code/matplotlib/clabel.py", line 27, in <module>
    ax.clabel(CS, CS.levels, inline=True, fmt=dict(zip(CS.levels, dates)),
  File "/home/elliott/code/matplotlib/lib/matplotlib/axes/_axes.py", line 6581, in clabel
    return CS.clabel(levels, **kwargs)
  File "/home/elliott/code/matplotlib/lib/matplotlib/contour.py", line 195, in clabel
    self.add_label_near(x, y, inline, inline_spacing)
  File "/home/elliott/code/matplotlib/lib/matplotlib/contour.py", line 553, in add_label_near
    x, y = transform.transform((x, y))
  File "/home/elliott/code/matplotlib/lib/matplotlib/transforms.py", line 1508, in transform
    res = self.transform_affine(self.transform_non_affine(values))
  File "/home/elliott/code/matplotlib/lib/matplotlib/_api/deprecation.py", line 297, in wrapper
    return func(*args, **kwargs)
  File "/home/elliott/code/matplotlib/lib/matplotlib/transforms.py", line 2422, in transform_affine
    return self.get_affine().transform(values)
  File "/home/elliott/code/matplotlib/lib/matplotlib/transforms.py", line 1797, in transform
    return self.transform_affine(values)
  File "/home/elliott/code/matplotlib/lib/matplotlib/_api/deprecation.py", line 297, in wrapper
    return func(*args, **kwargs)
  File "/home/elliott/code/matplotlib/lib/matplotlib/transforms.py", line 1868, in transform_affine
    return affine_transform(values, mtx)
TypeError: Cannot cast array data from dtype('O') to dtype('float64') according to the rule 'safe'
```
### Expected outcome

Labels are added at spots corresponding to those given in `manual`.

### Additional information

_No response_

### Operating system

_No response_

### Matplotlib Version

589d3fbe13f0067a21804ab3f55ffeb07a839b90

### Matplotlib Backend

_No response_

### Python version

_No response_

### Jupyter version

_No response_

### Installation

git checkout

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi [user] 
i would be interested in looking into this.
From the traceback, it seems like the manual label coordinates might not be going through unit conversion before being passed to the transform. Does that sound like the right place to start investigating?
Happy to put together a small fix and corresponding test if that’s the intended direction.

### Comment 2 ([user]):

[user] Yes, I'd say that might be the right place to start looking.

### Comment 3 ([user]):

hey [user] i have opened a PR for this... #31278

## PR Review Comments

**[user]** on `lib/matplotlib/contour.py`:

Maybe tangential, but does this if ever evaluate to false given lines 451-452?

**[user]** on `lib/matplotlib/tests/test_datetime.py`:

Can you test that the label is set to the expected value?

**[user]** on `lib/matplotlib/contour.py`:

`if transform:` can evaluate to False when `transform=False` is explicitly passed, which is used in `_contour_labeler_event_handler` for mouse click events(display coordinates)

**[user]** on `lib/matplotlib/tests/test_datetime.py`:

sure i can add an assertion on the label value, what would be the best way to check it, assert on the text string or the position?

**[user]** on `lib/matplotlib/tests/test_datetime.py`:

Both?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
