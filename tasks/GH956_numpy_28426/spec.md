# GH956_numpy_28426: BUG: Limit the maximal number of bins for automatic histogram binning — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/numpy/numpy/issues/28400
- Repo: https://github.com/numpy/numpy

## Issue Description

### Describe the issue:

For some data arrays, `np.histogram` tries to allocate absurd amount of memory and crashes. This happens with `bins = "auto"` and supposedly is a result of miscalculation of required number of bins. 

### Reproduce the code example:

```python
import numpy as np

Z = np.array(
    [
        1.99999999999995173450e-11,
        1.00000000000014130337e-11,
        1.99999999999995173450e-11,
        1.00000000000014130337e-11,
        1.99999999999995173450e-11,
        9.99999999999810431126e-12,
        2.00000000000028260674e-11,
        9.99999999999810431126e-12,
        1.99999999999995173450e-11,
        1.00000000000014130337e-11,
        1.99999999999995173450e-11,
        1.00000000000014130337e-11,
        1.99999999999995173450e-11,
        9.99999999999810431126e-12,
        2.00000000000028260674e-11,
        9.99999999999810431126e-12,
        1.00000000000014130337e-11,
        1.99999999999995173450e-11,
        1.99999999999995173450e-11,
        1.00000000000014130337e-11,
        9.99999999999810431126e-12,
        1.00000000000014130337e-11,
        1.99999999999995173450e-11,
        9.99999999999810431126e-12,
        2.00000000000028260674e-11,
        9.99999999999810431126e-12,
        1.99999999999995173450e-11,
        1.00000000000014130337e-11,
        1.99999999999995173450e-11,
        1.00000000000014130337e-11,
        9.99999999999810431126e-12,
        1.00000000000014130337e-11,
        9.99999999999810431126e-12,
        1.00000000000014130337e-11,
        1.99999999999995173450e-11,
        1.00000000000014130337e-11,
        1.99999999999995173450e-11,
        9.99999999999810431126e-12,
        1.00000000000014130337e-11,
        9.99999999999810431126e-12,
        1.00000000000014130337e-11,
        1.00000000000014130337e-11,
        9.99999999999810431126e-12,
        1.99999999999995173450e-11,
        1.00000000000014130337e-11,
        9.99999999999810431126e-12,
        1.00000000000014130337e-11,
        1.99999999999995173450e-11,
        1.00000000000014130337e-11,
        9.99999999999810431126e-12,
        1.00000000000014130337e-11,
        9.99999999999810431126e-12,
        2.00000000000028260674e-11,
        0.00000000000000000000e00,
        9.99999999999810431126e-12,
        1.00000000000014130337e-11,
        9.99999999999810431126e-12,
        1.00000000000014130337e-11,
        9.99999999999810431126e-12,
        1.00000000000014130337e-11,
        0.00000000000000000000e00,
        1.00000000000014130337e-11,
        9.99999999999810431126e-12,
        1.00000000000014130337e-11,
        1.99999999999995173450e-11,
        9.99999999999810431126e-12,
        0.00000000000000000000e00,
        1.00000000000014130337e-11,
        1.99999999999995173450e-11,
        0.00000000000000000000e00,
        1.00000000000014130337e-11,
        9.99999999999810431126e-12,
        1.00000000000014130337e-11,
        9.99999999999810431126e-12,
        1.00000000000014130337e-11,
        0.00000000000000000000e00,
        1.00000000000014130337e-11,
        9.99999999999810431126e-12,
        1.00000000000014130337e-11,
        9.99999999999810431126e-12,
        1.00000000000014130337e-11,
        9.99999999999810431126e-12,
        1.00000000000014130337e-11,
        1.00000000000014130337e-11,
        9.99999999999810431126e-12,
        1.00000000000014130337e-11,
        9.99999999999810431126e-12,
        1.00000000000014130337e-11,
        9.99999999999810431126e-12,
    ]
)

np.histogram(Z, bins="auto")
```

### Error message:

```shell
Traceback (most recent call last):
  File "/home/censored/bug.py", line 137, in <module>
    np.histogram(Z, bins="auto")
  File "/home/censored/.venv/lib/python3.12/site-packages/numpy/lib/histograms.py", line 780, in histogram
    bin_edges, uniform_bins = _get_bin_edges(a, bins, range, weights)
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/censored/.venv/lib/python3.12/site-packages/numpy/lib/histograms.py", line 446, in _get_bin_edges
    bin_edges = np.linspace(
                ^^^^^^^^^^^^
  File "/home/censored/.venv/lib/python3.12/site-packages/numpy/core/function_base.py", line 140, in linspace
    y = _nx.arange(0, num, dtype=dt).reshape((-1,) + (1,) * ndim(delta))
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
numpy.core._exceptions._ArrayMemoryError: Unable to allocate 98.2 TiB for an array with shape (13493864060128,) and data type float64
```

### Python and NumPy Versions:

1.26.4
3.12.7 (main, Feb  4 2025, 14:46:03) [GCC 14.2.0]


### Runtime Environment:

[{'numpy_version': '1.26.4',
  'python': '3.12.7 (main, Feb  4 2025, 14:46:03) [GCC 14.2.0]',
  'uname': uname_result(system='Linux', node='censored', release='6.11.0-14-generic', version='#15-Ubuntu SMP PREEMPT_DYNAMIC Fri Jan 10 23:48:25 UTC 2025', machine='x86_64')},
 {'simd_extensions': {'baseline': ['SSE', 'SSE2', 'SSE3'],
                      'found': ['SSSE3',
                                'SSE41',
                                'POPCNT',
                                'SSE42',
                                'AVX',
                                'F16C',
                                'FMA3',
                                'AVX2'],
                      'not_found': ['AVX512F',
                                    'AVX512CD',
                                    'AVX512_KNL',
                                    'AVX512_KNM',
                                    'AVX512_SKX',
                                    'AVX512_CLX',
                                    'AVX512_CNL',
                                    'AVX512_ICL']}},
 {'architecture': 'Zen',
  'filepath': '/home/censored/.venv/lib/python3.12/site-packages/numpy.libs/libopenblas64_p-r0-0cf96a72.3.23.dev.so',
  'internal_api': 'openblas',
  'num_threads': 16,
  'prefix': 'libopenblas',
  'threading_layer': 'pthreads',
  'user_api': 'blas',
  'version': '0.3.23.dev'}]

### Context for the issue:

_No response_

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

The issue is also present in numpy 2.x. Here is a bit smaller reproducer: 
```
import numpy as np
e = 1 + 1e-12
Z = [0,1,1,1,1,1,e,e,e,e,e,e, 2]
np.histogram(Z, bins="auto")
```
The problem is here:

https://github.com/numpy/numpy/blob/9e557eb0b621bbb92c4453b9674bb818c587845e/numpy/lib/_histograms_impl.py#L262-L269

The `_hist_bin_fd` takes the 25th and 75th percentile of the data (extremely small in the cases here) and uses that the calculate a bin width. If the 25th and 75th are equal, then `fd_bw` is zero so the output of `sturges_bw` is taken.

We could replace the condition `if fd_bw:` with 
```
if fd_bw < 1e-6 * (range[-1] - range[0]):
```
This would mean taking `sturges_bw` if the number of bins would up higher than 1 million. The `1e-6` is a bit arbitrary.

### Comment 2 ([user]):

I'm no expert, but there is a decent amount of literature on this topic.

One example (cited on the wikipedia page for the Freedman-Diaconis rule): http://www.numdam.org/item/10.1051/ps:2006001.pdf

I don't know if inserting another rule of thumb in this logic is necessarily going to avoid making other cases worse. The above paper notes that Freedman-Diaconis assumes the data are being sampled from a smooth distribution. Given the large dynamic range in the test data I don't think that's a good assumption. Maybe there's a more principled algorithm to determine if Freedman-Diaconis doesn't make sense?

### Comment 3 ([user]):

Also totally separately the `del range` stuff can probably go away - these are internal APIs, we should feel free to change them.

### Comment 4 ([user]):

For context this is not limited to Freedman-Diaconis bins but is an issue with all the "auto"-binning schemes. See also #15332.

### Comment 5 ([user]):

[user] I decided to add a rule of thumb which seems relaxed enough to keep the old behavior the normal cases, but which does avoid the out-of-memory issues. The rule is based on a maximum `n/log(n)` found in your reference "How many bins should be put in a regular histogram", ESAIM: Probability and Statistics, Volume 10 (2006), pp. 24-45, http://www.numdam.org/item/10.1051/ps:2006001.pdf

There is quite some literature available, but I suspect that what is a "normal case"  and what is a good number for auto binning is subjective at the end of the day, so maybe we can just use a simple rule for the auto binning.

## PR Review Comments

**[user]** on `numpy/lib/_histograms_impl.py`:

might as well 🤷🏻 

```suggestion
    maximum_number_of_bins = 2 * x.size / math.log1p(x.size)
```

**[user]** on `numpy/lib/_histograms_impl.py`:

Cool! Never knew people needed it so much to add a special method for it

**[user]** on `numpy/lib/_histograms_impl.py`:

Two comments:
1. The logarithm rule is basically the sturges rule, I think.  So I think you could just re-use that directly with some factor?  (I don't have an intuition for how the two rules behave, so not sure what this changes in practice yet.)
   There might be a fun difference, in that you use the range, and the sturges rule seems to calculate the min/max? 
3. percentile on the range seems odd, since it should just be two values.

(As said, didn't think about the actual heuristic choice yet, i.e. why does this mix fd and struges?  Is fd usually smaller or larger for "reasonable" data?)

**[user]** on `numpy/lib/_histograms_impl.py`:

```suggestion
    not result in a large number of bins. The relaxed Freedman-Diaconis estimator
    limits the bin width to half the sqrt estimated to avoid small bins.
```

**[user]** on `doc/release/upcoming_changes/28426.change.rst`:

```suggestion
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
