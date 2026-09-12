# GH873_scipy_24749: BUG: signal.minimum_phase: correct calculation — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/scipy/scipy/issues/22752
- Repo: https://github.com/scipy/scipy

## Issue Description

### Describe your issue.

The scipy.signal.minimum_phase seems to have an error when computing the homomorphic mask. This [line](https://github.com/scipy/scipy/blob/0f1fd4a7268b813fa2b844ca6038e4dfdf90084a/scipy/signal/_fir_filter_design.py#L1280) seems to be intended to check if the signal length is even, however the logic is backwards. This generates a ripple in the bandpass of the resulting minimum phase filter. See plot below.

![Image](https://github.com/user-attachments/assets/0e2e7872-cee6-4433-b2f2-ce7f481a3f9a)

If these two [lines](https://github.com/scipy/scipy/blob/0f1fd4a7268b813fa2b844ca6038e4dfdf90084a/scipy/signal/_fir_filter_design.py#L1279C9-L1280C22) are modified as follows:

```
win[1 : stop **+ 1**] = 2

        if n_fft % 2 **== 0**:
            win[stop] = 1
```
the resulting magnitude response of the minimum phase filter matches the expected result. see plot below. 

![Image](https://github.com/user-attachments/assets/c7372e50-c324-4fb4-87db-3ab6bae8120c)

### Reproducing Code Example

```python
import numpy as np
import matplotlib.pyplot as plt
import torch
from scipy.signal import minimum_phase

# Filter parameters
N = 963
fc = 0.13655297795265942  # Cutoff frequency Hz

# Ideal low-pass filter impulse response
n = torch.arange(N) - (N - 1) / 2
h_ideal = torch.sin(2 * np.pi * fc * n) / (n * np.pi)
h_ideal[(N - 1) // 2] = 2 * np.pi * fc / np.pi

# Hamming window
window = torch.hamming_window(N)

# Windowed impulse response
h = h_ideal * window
# scipy.signal minimum phase conversion
h_min_sig = minimum_phase(h, method="homomorphic", n_fft=N, half=False)

# Minimum phase comparison
plt.figure(figsize=(10, 8))
plt.subplot(3, 1, 1)
plt.stem(h, linefmt="k-", markerfmt="ko", basefmt="k-", label="original")
plt.stem(
    h_min_sig, linefmt="r--", markerfmt="ro", basefmt="r-", label="min-phase signal"
)
plt.xlabel("Sample Index (n)")
plt.ylabel("Amplitude")
plt.legend()
plt.grid(True)

plt.subplot(3, 1, 2)
plt.plot(torch.fft.fft(h).abs(), "k", label="original")
plt.plot(torch.fft.fft(torch.Tensor(h_min_sig), N).abs(), "r-.", label="min-phase sig")
plt.xlabel("Freq bin")
plt.ylabel("Amplitude")
plt.grid(True)
plt.legend()

plt.subplot(3, 1, 3)
plt.plot(np.unwrap(torch.fft.fft(h).angle()), "k", label="original")
plt.plot(
    np.unwrap(torch.fft.fft(torch.Tensor(h_min_sig), N).angle()),
    "r:",
    label="min-phase signal",
)
plt.xlabel("Freq bin")
plt.ylabel("Phase")
plt.grid(True)
plt.legend()

plt.show()
```

### Error message

```shell
NA
```

### SciPy/NumPy/Python version and system information

```shell
1.15.2 1.23.5 sys.version_info(major=3, minor=10, micro=12, releaselevel='final', serial=0)
Build Dependencies:
  blas:
    detection method: pkgconfig
    found: true
    include directory: /opt/_internal/cpython-3.10.15/lib/python3.10/site-packages/scipy_openblas32/include
    lib directory: /opt/_internal/cpython-3.10.15/lib/python3.10/site-packages/scipy_openblas32/lib
    name: scipy-openblas
    openblas configuration: OpenBLAS 0.3.28 DYNAMIC_ARCH NO_AFFINITY Haswell MAX_THREADS=64
    pc file directory: /project
    version: 0.3.28
  lapack:
    detection method: pkgconfig
    found: true
    include directory: /opt/_internal/cpython-3.10.15/lib/python3.10/site-packages/scipy_openblas32/include
    lib directory: /opt/_internal/cpython-3.10.15/lib/python3.10/site-packages/scipy_openblas32/lib
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
    version: 3.0.12
  fortran:
    commands: gfortran
    linker: ld.bfd
    name: gcc
    version: 10.2.1
  pythran:
    include directory: ../../tmp/pip-build-env-3bbjuwx1/overlay/lib/python3.10/site-packages/pythran
    version: 0.17.0
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
  path: /opt/python/cp310-cp310/bin/python
  version: '3.10'
```

## PR Review Comments

**[user]** on `scipy/signal/tests/test_fir_filter_design.py`:

```suggestion
    def test_nyquist(self, N, dtype, xp):
```

and remove the `xp = array_namespace` call below.

**[user]** on `scipy/signal/tests/test_fir_filter_design.py`:

`fc = xp.asarray(10)`

will do the right thing because https://github.com/scipy/scipy/blob/main/scipy/signal/_fir_filter_design.py#L476

**[user]** on `scipy/signal/tests/test_fir_filter_design.py`:

```suggestion
        h = xp.astype(h, xp_dtype)
```

**[user]** on `scipy/signal/tests/test_fir_filter_design.py`:

```suggestion
        H_mag = xp.abs(rfft(h, N))
```

**[user]** on `scipy/signal/tests/test_fir_filter_design.py`:

```suggestion
        H_min_mag = xp.abs(rfft(h_min_sig, N))
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
