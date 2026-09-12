# GH1070_numpy_31033: BUG: Fix `np.vecdot` on empty object vectors returning None — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/numpy/numpy/issues/31019
- Repo: https://github.com/numpy/numpy

## Issue Description

### Describe the issue:

For object arrays `x`, I expected `vecdot` to follow a definition like `np.sum(x*x)`, but this doesn't seem to hold when the length along `axis` is `0`. In this case, the result is `None` instead of `0`.

### Reproduce the code example:

```python
import numpy as np
x = np.empty((0,), dtype=object)
np.vecdot(x, x)  # None
x = np.empty((1, 0), dtype=object)
np.vecdot(x, x)  # array([None], dtype=object)
```

### Error message:

```shell

```

### Python and NumPy Versions:

2.3.5
3.13.12 | packaged by conda-forge | (main, Feb  5 2026, 05:41:12) [MSC v.1944 64 bit (AMD64)]

### Runtime Environment:

_No response_

### How does this issue affect you or how did you find it:

Discovered in the context of running https://github.com/mdhaber/mparray/ against array-api-tests. I can work around it by adding a special case, but it would be nice to have it fixed.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
