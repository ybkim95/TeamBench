# GH1042_matplotlib_31091: BUG: Fix IndexLocator.tick_values returning values greater than vmax — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/matplotlib/matplotlib/issues/31086
- Repo: https://github.com/matplotlib/matplotlib

## Issue Description

### Bug summary

When creating a colorbar using a ScalarMappable with the NoNorm normalization and a discrete colormap (e.g., viridis with a fixed number of colors), the ticks returned by the colorbar’s get_ticks() method do not align with the visually displayed tick positions. This will cause `cbar.set_ticks(cbar.get_ticks())` to change the ticks.

### Code for reproduction

```Python
import matplotlib.pyplot as plt
from matplotlib import cm, colors
data = [1, 2, 3, 4, 5]
fig, ax = plt.subplots()
cbar = fig.colorbar(cm.ScalarMappable(norm=colors.NoNorm(), cmap=plt.get_cmap("viridis", len(data))), ax=ax)
print(cbar.get_ticks())
cbar.set_ticks(cbar.get_ticks()) # this unexpectedly changes the ticks
```

### Actual outcome

[0. 1. 2. 3. 4. 5.]

<img width="510" height="418" alt="Image" src="https://github.com/user-attachments/assets/58104102-4fb1-42f9-8438-2fc5a8bf5c60" />

### Expected outcome

[0. 1. 2. 3. 4.]

<img width="510" height="418" alt="Image" src="https://github.com/user-attachments/assets/065c9d5f-1813-46ff-a687-543d7b45d14c" />

### Additional information

_No response_

### Operating system

_No response_

### Matplotlib Version

3.10.8

### Matplotlib Backend

_No response_

### Python version

_No response_

### Jupyter version

_No response_

### Installation

None

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

The technical reason is in `IndexLocator.tick_values`

https://github.com/matplotlib/matplotlib/blob/2b8103b1e4f393002b33a7802558031e7b88d2b2/lib/matplotlib/ticker.py#L1769-L1771

This should not return values > vmax. - For `NoNorm` we use an `IndexLocator(base=n, offset=0.5)`, where `n` is a reasonably calculated step size.

---
The other question is: What are you trying to do?

Note: While `cbar.set_ticks(cbar.get_ticks())` should not change the displayed ticks at that time, it internally changes from an `IndexLocator` to a `FixedLocator`, i.e. automatic tick placement is replaced by hard-coded tick positions, which may be undesirable.

### Comment 2 ([user]):

The behavior of `get_ticks()` should be consistent for different colorbars. But the actual result of `get_ticks()` for the discrete colorbar is inconsistent with the continuous colorbar. In the following example of the discrete colorbar, the result of `get_ticks()` contains 5.0, which should not be included since the discrete colorbar does not have a tick of 5.0.

```python
# Continuous colorbar
import matplotlib.pyplot as plt
from matplotlib import cm, colors
data = [1, 2, 3, 4, 5]
fig, ax = plt.subplots()
cbar = fig.colorbar(cm.ScalarMappable(norm=colors.NoNorm(), cmap=plt.get_cmap("viridis")), ax=ax)
print(cbar.get_ticks())
# Actual Output (Correct): [  0.  26.  52.  78. 104. 130. 156. 182. 208. 234.]
```
<img width="528" height="418" alt="Image" src="https://github.com/user-attachments/assets/4b5e2022-0393-4bc8-9c3f-71059b8d4caf" />

```python
# Discrete colorbar
import matplotlib.pyplot as plt
from matplotlib import cm, colors
data = [1, 2, 3, 4, 5]
fig, ax = plt.subplots()
cbar = fig.colorbar(cm.ScalarMappable(norm=colors.NoNorm(), cmap=plt.get_cmap("viridis", len(data))), ax=ax)
print(cbar.get_ticks())
# Actual Output (Wrong): [0. 1. 2. 3. 4. 5.]
```

<img width="510" height="418" alt="Image" src="https://github.com/user-attachments/assets/5905e62f-67eb-4609-8065-a1f20641d176" />

### Comment 3 ([user]):

[user] I'm not following. The difference between your two examples is that you use the default colormap (which has N=256 values) and a resampled version with just N=5 values.

What the colorbar (or rather the IndexLocator used in case of NoNorm) does is select a "nice" set of indices between 0 and N-1. - At least that's the intention, but as explained in https://github.com/matplotlib/matplotlib/issues/31086#issuecomment-3853022532 the current implementation may create one extra index above N-1, depending on parameters.

## PR Review Comments

**[user]** on `lib/matplotlib/ticker.py`:

We can directly generate the right amount of ticks. No need for filtering.
```suggestion
        # We want tick values in the closed interval [vmin, vmax].
        # Since np.arange(start, stop) returns values in the semi-open interval
        # [start, stop), we add a minimal offset so that stop = vmax + eps
        tick_values = np.arange(vmin + self.offset, vmax + 1e-12, self._base)
        return self.raise_if_exceeds(tick_values)
```

**[user]** on `lib/matplotlib/tests/test_ticker.py`:

```suggestion
```
We don't need to reference (clutter) issues in code. This would also not be there if we had written the correct logic and test in the first place. Via git blame and Github, you can always reconstruct the PR and associated issue if needed.

**[user]** on `lib/matplotlib/tests/test_ticker.py`:

```suggestion
        assert_array_equal(index.tick_values(0, 4), [0, 1, 2, 3, 4])
```
The t<4 seems specifically motivated by the bug. If anything, we'd need to 0 <= t <= 4. But OTOH, the comparison to the fixed numbers already covers that check. One could argue that the check makes the logic range constraint explicit. But with that argument, one could also argue to check that all numbers are integer, and that they are monotonically increasing, and ...
So I claim the direct comparison with the expected result is sufficient.

Note: `assert_array_equal` is imported at the top, so we can keep this more compact.

Same for the following two tests.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
