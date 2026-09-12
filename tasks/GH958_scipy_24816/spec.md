# GH958_scipy_24816: BUG: sparse.csgraph.reconstruct_path: raise for non-integral predecessors — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/scipy/scipy/issues/23577
- Repo: https://github.com/scipy/scipy

## Issue Description

### Describe your issue.

`scipy.sparse.csgraph.reconstruct_path` causes a **Segmentation Fault** (core dumped) when `predecessors` is a float array containing `np.nan`.


### Reproducing Code Example

```python
import numpy as np
import scipy
from scipy.sparse import csr_matrix

row_indices = [0, 1, 1, 3, 3]
col_indices = [0, 2, 3, 1, 4]
data = [9, -6, -8, 6, 8]
matrix = csr_matrix((data, (row_indices, col_indices)), shape=(5, 5), dtype='int64')
predecessors = np.array([np.nan, np.nan, np.nan], dtype='float32')
x = scipy.sparse.csgraph.reconstruct_path(matrix, predecessors)
print(x)
```

### Error message

```shell
/path/to/lib/python3.12/site-packages/scipy/sparse/_compressed.py:561: RuntimeWarning: invalid value encountered in cast
  major = np.asarray(major, dtype=idx_dtype)
Segmentation fault (core dumped)
```

### SciPy/NumPy/Python version and system information

<details>

```shell
1.16.0 2.2.6 sys.version_info(major=3, minor=12, micro=0, releaselevel='final', serial=0)
Build Dependencies:
  blas:
    detection method: pkgconfig
    found: true
    include directory: /opt/_internal/cpython-3.12.11/lib/python3.12/site-packages/scipy_openblas32/include
    lib directory: /opt/_internal/cpython-3.12.11/lib/python3.12/site-packages/scipy_openblas32/lib
    name: scipy-openblas
    openblas configuration: OpenBLAS 0.3.28 DYNAMIC_ARCH NO_AFFINITY Haswell MAX_THREADS=64
    pc file directory: /project
    version: 0.3.28
  lapack:
    detection method: pkgconfig
    found: true
    include directory: /opt/_internal/cpython-3.12.11/lib/python3.12/site-packages/scipy_openblas32/include
    lib directory: /opt/_internal/cpython-3.12.11/lib/python3.12/site-packages/scipy_openblas32/lib
    name: scipy-openblas
    openblas configuration: OpenBLAS 0.3.28 DYNAMIC_ARCH NO_AFFINITY Haswell MAX_THREADS=64
    pc file directory: /project
    version: 0.3.28
  pybind11:
    detection method: config-tool
    include directory: unknown
    name: pybind11
    version: 2.13.6
Compilers:
  c:
    commands: cc
    linker: ld.bfd
    name: gcc
    version: 10.2.1
  c++:
    commands: c++
    linker: ld.bfd
    name: gcc
    version: 10.2.1
  cython:
    commands: cython
    linker: cython
    name: cython
    version: 3.1.2
  fortran:
    commands: gfortran
    linker: ld.bfd
    name: gcc
    version: 10.2.1
  pythran:
    include directory: ../../tmp/build-env-ltl35zwt/lib/python3.12/site-packages/pythran
    version: 0.18.0
Machine Information:
  build:
    cpu: x86_64
    endian: little
    family: x86_64
    system: linux
  cross-compiled: false
  host:
    cpu: x86_64
    endian: little
    family: x86_64
    system: linux
Python Information:
  path: /tmp/build-env-ltl35zwt/bin/python
  version: '3.12'
```

</details>

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I've done a bit of debugging on this issue. Here's what I've figured out so far.

 * The error happens when in `csr_sample_values()`. The method is passed a column index of -2147483648.
 * It is passed this because NumPy is attempting to convert NaN into an int32. There is of course no integer that can represent NaN, which causes the following warning:

   ```
   /home/nodell/scipy/build-install/usr/lib/python3.13/site-packages/scipy/sparse/_compressed.py:561: RuntimeWarning: invalid    value encountered in cast
     major = np.asarray(major, dtype=idx_dtype)
   ```

   Then, the value in the array is set to `0x80000000`.

Two ideas for a fix:

 * Forbid floating point input within the `predecessors` argument to `reconstruct_path()`. This works with all of the tests, but it is technically a breaking API change, because `csr_array.__getitem__()` will implicitly convert floating point indexes into integer indexes.
 * Within `_asindices()`, forbid NaN values in addition to doing range checks. A slightly more general fix with perhaps more performance cost.

### Comment 2 ([user]):

Thanks [user] for reporting this!

Of the two ideas for a fix [user] I have a slight preference for the second (forbidding `NaN` index values) which changes `_asindices()`.  If floats get converted to integers for index-values for csr_array, we will need to handle NaN. And raising seems like the only way to handle that kind of input.

### Comment 3 ([user]):

I looked at this issue, and while it's Hypothesis-generated (see https://github.com/scipy/scipy/issues/23555#issuecomment-3288578297) so not high prio, this one may be realistic enough to keep open and address.

I'd be fine with forbidding all floating-point arrays for arguments that require indices. NumPy no longer allows this either after all for regular indexing:
```
>>> import numpy as np
>>> x = np.arange(5)
>>> x[1.5]
Traceback (most recent call last):
  Cell In[9], line 1
    x[1.5]
IndexError: only integers, slices (`:`), ellipsis (`...`), numpy.newaxis (`None`) and integer or boolean arrays are valid indices

>>> idx = np.array([0, 2])
>>> x[idx]
array([0, 2])
>>> x[idx.astype(np.float64)]
Traceback (most recent call last):
  Cell In[12], line 1
    x[idx.astype(np.float64)]
IndexError: arrays used as indices must be of integer (or boolean) typ
```

The second option, doing `nan` checks, is indeed very expensive and doesn't seem like a reasonable solution for checking indexing arguments in general.

## PR Review Comments

**[user]** on `scipy/sparse/csgraph/_tools.pyx`:

This would be the only use of `np.isdtype` in our source outside of tests it seems, based on local `git grep`, but seems to do the job.

**[user]** on `scipy/sparse/csgraph/tests/test_conversions.py`:

Reverting the patch no longer causes this to fail with a segfault on my local machine, but it does still error, which is good enough.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
