# GH925_numpy_31049: BUG: Add test to reproduce problem described in #30816 (#30818) — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/numpy/numpy/issues/30816
- Repo: https://github.com/numpy/numpy

## Issue Description

### Describe the issue:

After updating to 2.4.2, we have noticed that `np.linalg.norm` returns a different value on the `ubuntu-24.04-arm` runner.

In particular, the code below runs successfully on the `ubuntu-24.04`, `macos-15`, `macos-15-intel`, and `windows-2025` runners. On the `ubuntu-24.04-arm` runner, it raises an assertion error and says that `norm = nan`. Other test cases have returned numeric values that differ significantly from those returned on the other runners. Downgrading to 2.4.1 resolves the issue.

The test file can be found here: https://github.com/denialhaag/numpy/blob/8a9f9f55f14e65382aea791f209041652308562a/numpy/tests/test_array.npy

### Reproduce the code example:

```python
from pathlib import Path

import numpy as np

test_array_path = Path(__file__).parent / "test_array.npy"
test_array = np.load(test_array_path)
norm = np.linalg.norm(test_array)
print(f"norm = {norm}")
assert np.isclose(norm, 1.0)
```

### Python and NumPy Versions:

Python versions: 3.11, 3.12, 3.13, and 3.14
NumPy version: 2.4.2


### Runtime Environment:

_No response_

### How does this issue affect you or how did you find it:

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

[user] I am assuming you mean the wheel install?  That would seem to indicate there is a bug with OpenBLAS vector product.
(That, or the bug would have to be `np.sqrt()` or just `np.add`, seems unlikely that this changed between 2.4.1 and 2.4.2, though.  I think we did bump the OpenBLAS to fix another issue, though.  CC [user])

### Comment 2 ([user]):

> [user] I am assuming you mean the wheel install? That would seem to indicate there is a bug with OpenBLAS vector product. (That, or the bug would have to be `np.sqrt()` or just `np.add`, seems unlikely that this changed between 2.4.1 and 2.4.2, though. I think we did bump the OpenBLAS to fix another issue, though. CC [user])

I might be misunderstanding the question, but the problem appears during execution.

I have run the example described above in our CI, and the corresponding test fails here: https://github.com/munich-quantum-toolkit/qudits/actions/runs/21901941709/job/63232264663#step:12:198

The same test passes on all other tested platforms (see the green checkmarks on the left).

Edit: I'm not sure exactly how your CI is configured, but I hope #30818 reproduces the error.

### Comment 3 ([user]):

The question is: How did you install NumPy without that information we don't even know if this issue has anything to do with NumPy at all.

I can trigger CI, but I am not optimistic, your test doesn't look particularly special (but it may be that we don't have larger arrays that are tested already).

### Comment 4 ([user]):

> The question is: How did you install NumPy without that information we don't even know if this issue has anything to do with NumPy at all.

Ahh, sorry, NumPy is simply installed from PyPI via `uv pip`.

### Comment 5 ([user]):

OK, I suppose we can start trying around a bit with typical openblas things.  E.g. running with `OPENBLAS_NUM_THREADS=1`.

Can you also check if `np.show_runtime()` shows something nice (after installing `threadpoolctl`)?

### Comment 6 ([user]):

> OK, I suppose we can start trying around a bit with typical openblas things. E.g. running with `OPENBLAS_NUM_THREADS=1`.

Running with `OPENBLAS_NUM_THREADS=1` has fixed the issue in our tests!

> Can you also check if `np.show_runtime()` shows something nice (after installing `threadpoolctl`)?

```
[{'numpy_version': '2.4.2',
  'python': '3.14.3 (main, Feb  3 2026, 22:54:07) [Clang 21.1.4 ]',
  'uname': uname_result(system='Linux', node='runnervmksr2l', release='6.14.0-1017-azure', version='#17~24.04.1-Ubuntu SMP Tue Dec  2 18:52:52 UTC 2025', machine='aarch64')},
 {'simd_extensions': {'baseline': ['NEON', 'NEON_FP16', 'NEON_VFPV4', 'ASIMD'],
                      'found': ['ASIMDHP', 'ASIMDDP', 'ASIMDFHM', 'SVE'],
                      'not_found': []}},
 {'ignore_floating_point_errors_in_matmul': False},
 {'architecture': 'neoversev2',
  'filepath': '/home/runner/work/qudits/qudits/.nox/tests-3-14/lib/python3.14/site-packages/numpy.libs/libscipy_openblas64_-e5a4d414.so',
  'internal_api': 'openblas',
  'num_threads': 1,
  'prefix': 'libscipy_openblas',
  'threading_layer': 'pthreads',
  'user_api': 'blas',
  'version': '0.3.31.dev'},
 {'architecture': 'neoversev2',
  'filepath': '/home/runner/work/qudits/qudits/.nox/tests-3-14/lib/python3.14/site-packages/scipy.libs/libscipy_openblas-c5a9b014.so',
  'internal_api': 'openblas',
  'num_threads': 1,
  'prefix': 'libscipy_openblas',
  'threading_layer': 'pthreads',
  'user_api': 'blas',
  'version': '0.3.30'}]
```

### Comment 7 ([user]):

CC [user] for awareness of apparently OpenBLAS issues (with threads?) on linux arm.

### Comment 8 ([user]):

Hmm. Nothing immediately obvious in 0.3.31, in particular nothing that wouldn't also blow up on other architectures. Not sure what exactly the "0.3.31.dev" snapshot is - if we're talking about vector norm, I changed the ARM64 SNRM2 a month ago to do the accumulation in double precision, but any breakage introduced there would affect single-threaded operation too.

### Comment 9 ([user]):

Glancing at the code what this uses under the hood should be double vector multiplication with a step size/stride of 2 (i.e. from `arr1.real * arr2.imag`).  I guess that also means that the `imag` one is only aligned to itemsize, if that matters.

### Comment 10 ([user]):

> Not sure what exactly the "0.3.31.dev" snapshot is

In the NumPy PyPI 2.4.2 release, we used `scipy-openblas64=0.3.31.22.1`, and that release of scipy-openblas uses OpenBLAS at commit `5ffbf38b`.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
