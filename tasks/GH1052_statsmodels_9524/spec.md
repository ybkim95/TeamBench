# GH1052_statsmodels_9524: BUG: Fix bug in Runs.runs_test for the case of a single run yielding … — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/statsmodels/statsmodels/issues/9523
- Repo: https://github.com/statsmodels/statsmodels

## Issue Description

#### Describe the bug

When a single run is provided, e.g. np.ones(50), resulting zscore and pvalue are (nan,nan)

This is not correct. Binomial theory tells us exactly what the probability of a single run of length n is, and we can calculate the matching z-score using the normal approximation.

#### Code Sample, a copy-pastable example if possible

```python
import numpy as np
from statsmodels.sandbox.stats.runs import runstest_1samp
print(runstest_1samp(np.ones(50)))
```

If the issue has not been resolved, please file it in the issue tracker.

#### Expected Output

A valid z-score and p-value should result. The existing implementation calculates zero variance, therefore divide-by-zero for the z-score, and resulting error in p-value. By catching this case of a single run, we can switch to exact calculation of p-value.

#### Output of ``import statsmodels.api as sm; sm.show_versions()``

INSTALLED VERSIONS
------------------
Python: 3.10.16.final.0
OS: Linux 6.8.0-52-generic #53~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Wed Jan 15 19:18:46 UTC 2 x86_64
byteorder: little
LC_ALL: None
LANG: en_GB.UTF-8

statsmodels
===========

Installed: 0.14.4 (/home/shamus/mambaforge/lib/python3.10/site-packages/statsmodels)

Required Dependencies
=====================

cython: Not installed
numpy: 1.26.4 (/home/shamus/mambaforge/lib/python3.10/site-packages/numpy)
scipy: 1.15.1 (/home/shamus/mambaforge/lib/python3.10/site-packages/scipy)
pandas: 2.2.3 (/home/shamus/mambaforge/lib/python3.10/site-packages/pandas)
    dateutil: 2.9.0.post0 (/home/shamus/mambaforge/lib/python3.10/site-packages/dateutil)
patsy: 1.0.1 (/home/shamus/mambaforge/lib/python3.10/site-packages/patsy)

Optional Dependencies
=====================

matplotlib: 3.10.0 (/home/shamus/mambaforge/lib/python3.10/site-packages/matplotlib)
    backend: module://matplotlib_inline.backend_inline 
cvxopt: Not installed
joblib: 1.4.2 (/home/shamus/mambaforge/lib/python3.10/site-packages/joblib)

Developer Tools
================

IPython: 8.32.0 (/home/shamus/mambaforge/lib/python3.10/site-packages/IPython)
    jinja2: 3.1.5 (/home/shamus/mambaforge/lib/python3.10/site-packages/jinja2)
sphinx: Not installed
    pygments: 2.19.1 (/home/shamus/mambaforge/lib/python3.10/site-packages/pygments)
pytest: 8.3.5 (/home/shamus/mambaforge/lib/python3.10/site-packages/pytest)
virtualenv: Not installed

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Proposed fix in PR #9524

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
