# GH1105_matplotlib_31203: Fix Axes.hist crash for numpy timedelta64 inputs — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/matplotlib/matplotlib/issues/31182
- Repo: https://github.com/matplotlib/matplotlib

## Issue Description

### Bug summary

I expected `ax.hist([sequence of timedeltas])` to Just Work, as it does with `ax.hist([sequence of timestamps])`. However, there is a comparison with `np.inf` that works when the sequence is of timestamps and fails when the sequence is of timedeltas; numpy cannot promote a `TimeDelta64DType` to a float: https://github.com/matplotlib/matplotlib/blob/main/lib/matplotlib/axes/_axes.py#L7479

### Code for reproduction

```Python
import matplotlib.pyplot as plt
import pandas as pd
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(1, 1, 1)
ax.hist(pd.date_range("2026-01-01", "2026-01-05", freq="D"))
ax.hist(pd.date_range("2026-01-01", "2026-01-05", freq="D").diff(1))
```

### Actual outcome

```
numpy.exceptions.DTypePromotionError: The DType <class 'numpy.dtypes.TimeDelta64DType'> could not be promoted by <class 'numpy.dtypes._PyFloatDType'>. This means that no common DType exists for the given inputs. For example they cannot be stored in a single array unless the dtype is `object`. The full list of DTypes is: (<class 'numpy.dtypes.TimeDelta64DType'>, <class 'numpy.dtypes._PyFloatDType'>)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "<python-input-5>", line 1, in <module>
    ax.hist(pd.date_range("2026-01-01", "2026-01-05", freq="D").diff(1))
    ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/kylepenner/Documents/numpy/lib/python3.13/site-packages/matplotlib/_api/deprecation.py", line 477, in wrapper
    return func(*args, **kwargs)
  File "/Users/kylepenner/Documents/numpy/lib/python3.13/site-packages/matplotlib/__init__.py", line 1497, in inner
    return func(
        ax,
        *map(cbook.sanitize_sequence, args),
        **{k: cbook.sanitize_sequence(v) for k, v in kwargs.items()})
  File "/Users/kylepenner/Documents/numpy/lib/python3.13/site-packages/matplotlib/axes/_axes.py", line 7479, in hist
    xmin = min(xmin, np.nanmin(xi))
numpy._core._exceptions._UFuncNoLoopError: ufunc 'less' did not contain a loop with signature matching types (<class 'numpy.dtypes.TimeDelta64DType'>, <class 'numpy.dtypes._PyFloatDType'>) -> None
```


### Expected outcome

There's an easy way around this---convert the timedeltas to floats with `.total_seconds()`---but I do prefer the `hist` call to just work.

### Additional information

_No response_

### Operating system

_No response_

### Matplotlib Version

3.11.0.dev1799+g6dbc0c7cd

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

Hii
I reproduce this issue on current main.

 ### Environment:
* Python 3.12
* Linux (Ubuntu)
* Matplotlib built from source

The failure occurs during histogram range computation in `Axes.hist `, where `xmin = np.inf` and `xmax = -np.inf` are initialized and later compared against `numpy.timedelta64`. After `_process_unit_info` and `convert_xunits`, the data still contains `timedelta64`, so the min/max logic involving `np.inf` triggers the `DTypePromotionError`.

I'm looking into adjusting the range computataion to avoid comparisons with `np.inf` for non-numeric dtypes.

### Comment 2 ([user]):

Hi, I also reproduced this on main (Python 3.11, macOS).
It looks like the failure originates from comparisons with np.inf during range computation when the dtype remains timedelta64.
[user] Are you actively working on a fix? If not, I’d be happy to investigate further and propose one.

### Comment 3 ([user]):

[user]    **Yes ,** I'm actively working on a fix and looking into improving the range computation for non-numeric dtypes like `timedelta64`. I'll update with a proposed fix.

### Comment 4 ([user]):

to give you an expectation for your solution from the user side: the `ax.hist(pd.date_range("2026-01-01", "2026-01-05", freq="D"))` call produces a plot with x axis ticks formatted for datetimes, see attached. I'd like the timedelta call to result in a plot with x axis ticks formatted for timedeltas, in a similar vein.

<img width="1000" height="700" alt="Image" src="https://github.com/user-attachments/assets/56a55db3-59d6-4491-9d5f-30cf782f5456" />

### Comment 5 ([user]):

[user] Thanks for the clarification. I understand the goal is not just to avoid failure, but to have `ax.hist` handle timedeltas with proper axis formatting, similar to datetimes. I'll investigate how datetime unit conversion is integrated in `hist` and whether the same units mechanism can be extended to timedeltas.

### Comment 6 ([user]):

Timedeltas are not handled well in general, and I'm a little skeptical that just fixing the crash will give expected results. [user], could you please share what a histogram looks like with your fix applied?

Relevant issue tracking timedelta things: https://github.com/matplotlib/matplotlib/issues/8869

### Comment 7 ([user]):

<img width="654" height="559" alt="Image" src="https://github.com/user-attachments/assets/ea3e5232-6521-4053-982c-9eb2efae8c72" />

With the current patch, `numpy.timedelta64` values are normalized to days before range estimation and binning. The histogram renders without crashing, and bin positions correspond to day values.

This change strictly addresses the crash caused by comparison with `np.inf` , and enables basic histogram computation for `timedelta64` inputs.
It does not yet integrate with matplotlib's unit conversion system , so the axis is displayed as numeric day values rather than a timedelta-aware  formatter.

If the preferred direction is to support full timedelta unit handling (as in #8869), I 'd happy to explore integrating this more deeply with the unit conversion machinery instead of converting to floats.

### Comment 8 ([user]):

We at least in some places accept timedelta, e.g. `plt.bar(['A', 'B', 'C'], np.array([1, 2, 4], dtype=np.timedelta64))`.

I'm not clear whether this is just an implicit `array.astype(float)` (and whether that's generally sufficient) or whether we need more systematic unit handling.

### Comment 9 ([user]):

I do not think that the approach in #31293 is the correct one. Instead, I would use a different computation of xmin and xmax when we have timedelta64. np.min and np.max should The rest will probably "just work".

Also, there is no need to ravel/flatten. "The default is to compute the minimum of the flattened array."

### Comment 10 ([user]):

Also, note that the whole point of the `if bin_range is None:` check is to figure out if there are finite elements in x and in that case output a range. The only case it will not return a new `bin_range` is if the array is empty or only consists of nans.

## PR Review Comments

**[user]** on `lib/matplotlib/axes/_axes.py`:

This is unnecessary. `cbook._reshape_2D()` already returns a list of arrays.

So at least

```python
x = [arr / np.timedelta64(1, 'D') if np.issubdtype(arr.dtype, np.timedelta64) else arr
     for arr in x]
```
is possible.

---

Another question to be investigated: Is `arr / np.timedelta64(1, 'D')` equivalent to `arr.astype(float)` for timedelta arrays? If so, would a general `x = [arr.astype(float) for arr in x]` be reasonable?

**[user]** on `lib/matplotlib/axes/_axes.py`:

I'm confused: Isn't it enough to either convert the timedelta to numbers above *or* remove the comparision with np.inf though min/max here? Why do we need both changes?

**[user]** on `lib/matplotlib/axes/_axes.py`:

> Is `arr / np.timedelta64(1, 'D')` equivalent to `arr.astype(float)` for timedelta arrays?

No, which is the whole problem here. If it was possible to cast timedelta64 to float, the comparison would work.

**[user]** on `lib/matplotlib/axes/_axes.py`:

`astype(float)` [is valid](https://numpy.org/doc/stable/reference/arrays.datetime.html#converting-datetime-and-timedelta-to-python-object), and I think is the better solution.  Dividing by one day is going to give you tiny numbers if you started with seconds, and is going to error if you started with months or years.

**[user]** on `lib/matplotlib/axes/_axes.py`:

`astype(float)` is unsafe so if you choose to cast in this function you should be explicit in the documentation

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
