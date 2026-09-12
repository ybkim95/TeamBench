# GH1141_scipy_24108: Fix endpoints normalization for assoc_legendre_p — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/scipy/scipy/issues/24099
- Repo: https://github.com/scipy/scipy

## Issue Description

### Describe your issue.

The `assoc_legendre_p` function (and similarly, `assoc_legendre_p_all`) provides the option to normalize the output, which should be a straightforward multiplication of each function by a constant. For example, plotting `x,p(x)` and `x,p_norm(x)` should differ everywhere by a constant.

As you can see from the image below or by running the code example, this is correct everywhere **except** at the endpoints, e.g. x=-1, x=1 (I'm using this for spherical harmonics, so parameterized those with cos(theta)). Perhaps a normalization loop is starting/ending 1 index too early?

<img width="549" height="414" alt="Image" src="https://github.com/user-attachments/assets/4dcb6633-c6a1-4f1a-ab65-17b50d2cdb20" />

### Reproducing Code Example

```python
import numpy as np
import scipy
import matplotlib.pyplot as plt

n=2
m=0
theta=np.linspace(0,np.pi,num=100)
Pl=scipy.special.assoc_legendre_p(n,m,np.cos(theta),diff_n=0,norm=False)
Pl_norm=scipy.special.assoc_legendre_p(n,m,np.cos(theta),diff_n=0,norm=True)

plt.figure()
plt.plot(theta,Pl[0,:])
plt.plot(theta,Pl_norm[0,:])
plt.show()
```

### Error message

```shell
N/A
```

### SciPy/NumPy/Python version and system information

```shell
1.16.2 2.2.6 sys.version_info(major=3, minor=12, micro=3, releaselevel='final', serial=0)
Build Dependencies:
  blas:
    detection method: pkgconfig
    found: true
    include directory: /opt/_internal/cpython-3.12.11/lib/python3.12/site-packages/scipy_openblas32/include
    lib directory: /opt/_internal/cpython-3.12.11/lib/python3.12/site-packages/scipy_openblas32/lib
    name: scipy-openblas
    openblas configuration: OpenBLAS 0.3.29.dev DYNAMIC_ARCH NO_AFFINITY Haswell MAX_THREADS=64
    pc file directory: /project
    version: 0.3.29.dev
  lapack:
    detection method: pkgconfig
    found: true
    include directory: /opt/_internal/cpython-3.12.11/lib/python3.12/site-packages/scipy_openblas32/include
    lib directory: /opt/_internal/cpython-3.12.11/lib/python3.12/site-packages/scipy_openblas32/lib
    name: scipy-openblas
    openblas configuration: OpenBLAS 0.3.29.dev DYNAMIC_ARCH NO_AFFINITY Haswell MAX_THREADS=64
    pc file directory: /project
    version: 0.3.29.dev
  pybind11:
    detection method: config-tool
    include directory: unknown
    name: pybind11
    version: 3.0.1
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
    version: 3.1.3
  fortran:
    commands: gfortran
    linker: ld.bfd
    name: gcc
    version: 10.2.1
  pythran:
    include directory: ../../tmp/build-env-rkdsvvju/lib/python3.12/site-packages/pythran
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
  path: /tmp/build-env-rkdsvvju/bin/python
  version: '3.12'
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

take

## PR Review Comments

**[user]** on `scipy/special/tests/test_legendre.py`:

nit, here the `pytest.mark.parametrize` doesn't do anything because there is only one value passed

**[user]** on `scipy/special/tests/test_legendre.py`:

Sorry for that, see below [user]. Thanks.

**[user]** on `scipy/special/tests/test_legendre.py`:

You could parametrize both tests over `n` to get better testing feedback if only a subset of cases start failing at some point, but not sure that is even worth flushing the CI again over.

**[user]** on `scipy/special/tests/test_legendre.py`:

[user] thanks. I've added your suggestion and removed the for loop. Let me know if that works for you.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
