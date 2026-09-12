# GH467_pandas_61920: BUG: IntervalIndex.unique() only contains the first interval if all interval borders are negative — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pandas-dev/pandas/issues/61917
- Repo: https://github.com/pandas-dev/pandas

## Issue Description

### Pandas version checks

- [x] I have checked that this issue has not already been reported.

- [x] I have confirmed this bug exists on the [latest version](https://pandas.pydata.org/docs/whatsnew/index.html) of pandas.

- [x] I have confirmed this bug exists on the [main branch](https://pandas.pydata.org/docs/dev/getting_started/install.html#installing-the-development-version-of-pandas) of pandas.

### Reproducible Example

```python
import pandas as pd

print(pd.__version__)

idx_pos = pd.IntervalIndex.from_tuples([(3, 4), (3, 4), (2, 3), (2, 3), (1, 2), (1, 2)])

print(idx_pos.unique())
assert idx_pos.unique().shape == (3,)  # succeeds

idx_neg = pd.IntervalIndex.from_tuples([(-4, -3), (-4, -3), (-3, -2), (-3, -2), (-2, -1), (-2, -1)])

print(idx_neg.unique())
assert idx_neg.unique().shape == (3,), f"Actual shape: {idx_neg.unique().shape}"
```

### Issue Description

Output with current main:

```
3.0.0.dev0+2250.g13f7b8b7e3
IntervalIndex([(3, 4], (2, 3], (1, 2]], dtype='interval[int64, right]')
IntervalIndex([(-4, -3]], dtype='interval[int64, right]')
Traceback (most recent call last):
  File "/home/jmu3si/tmp/pd-demo.py", line 12, in <module>
    assert idx_neg.unique().shape == (3,), f"Actual shape: {idx_neg.unique().shape}"
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Actual shape: (1,)
```

Only the interval `(-4, 3]` appears in the uniqued index.

A couple of other observations:

* The same result occurs with `closed="left"`
* Intervals that are not fully negative, e.g. `(-2, 0]` also appear in the uniqued index
* This does not seem to be a regression. I reproduced it all the way back to pandas-1.4.3

### Expected Behavior

Expect correct unique index for `index_neg` to be 

`IntervalIndex([(-4, -3], (-3, -2], (-2, -1]], dtype='interval[int64, right]')` as it correctly did with the positive interval index.

### Installed Versions

<details>

INSTALLED VERSIONS
------------------
commit                : 13f7b8b7e3dc6695c4e4b00afd0cccbd754210bd
python                : 3.13.2
python-bits           : 64
OS                    : Linux
OS-release            : 6.8.0-60-generic
Version               : #63~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Tue Apr 22 19:00:15 UTC 2
machine               : x86_64
processor             : x86_64
byteorder             : little
LC_ALL                : None
LANG                  : de_DE.UTF-8
LOCALE                : de_DE.UTF-8

pandas                : 3.0.0.dev0+2250.g13f7b8b7e3
numpy                 : 2.2.6
dateutil              : 2.9.0.post0
pip                   : 25.1.1
Cython                : 3.1.2
sphinx                : 8.2.3
IPython               : 9.4.0
adbc-driver-postgresql: None
adbc-driver-sqlite    : None
bs4                   : 4.13.4
bottleneck            : 1.5.0
fastparquet           : 2024.11.0
fsspec                : 2025.7.0
html5lib              : 1.1
hypothesis            : 6.136.1
gcsfs                 : 2025.7.0
jinja2                : 3.1.6
lxml.etree            : 6.0.0
matplotlib            : 3.10.3
numba                 : 0.61.2
numexpr               : 2.11.0
odfpy                 : None
openpyxl              : 3.1.5
psycopg2              : 2.9.10
pymysql               : 1.4.6
pyarrow               : 21.0.0
pyiceberg             : 0.9.1
pyreadstat            : 1.3.0
pytest                : 8.4.1
python-calamine       : None
pytz                  : 2025.2
pyxlsb                : 1.0.10
s3fs                  : 2025.7.0
scipy                 : 1.16.0
sqlalchemy            : 2.0.41
tables                : 3.10.2
tabulate              : 0.9.0
xarray                : 2025.7.1
xlrd                  : 2.0.2
xlsxwriter            : 3.2.5
zstandard             : 0.23.0
qtpy                  : None
pyqt5                 : None

</details>

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I think the issue is with this logic:

https://github.com/pandas-dev/pandas/blob/073710f6be25ff7b402314be40af4e5c80e522d3/pandas/core/arrays/interval.py#L1992-L2000

Test Script:
```python
import pandas as pd
idx_pos = pd.IntervalIndex.from_tuples([(3, 4), (3, 4), (2, 3), (2, 3), (1, 2), (1, 2)])
print(idx_pos)

ia = idx_pos._data

print("\nCombined (ia._combined):")
print(ia._combined)

combined_view = ia._combined.view("complex128")
print("\ncombined_view (as complex128):")
print(combined_view)

print("idx_pos unique()")
print(idx_pos.unique())

print("-------------------------------------------------------------------")

idx_neg = pd.IntervalIndex.from_tuples([(-4, -3), (-4, -3), (-3, -2), (-3, -2), (-2, -1), (-2, -1)])
print(idx_neg)
ia = idx_neg._data

print("\nCombined (ia._combined):")
print(ia._combined)

combined_view = ia._combined.view("complex128")
print("\ncombined_view (as complex128):")
print(combined_view)
print("idx_neg unique()")
print(idx_neg.unique())

```

Output:

```
IntervalIndex([(3, 4], (3, 4], (2, 3], (2, 3], (1, 2], (1, 2]], dtype='interval[int64, right]')

Combined (ia._combined):
[[3 4]
 [3 4]
 [2 3]
 [2 3]
 [1 2]
 [1 2]]

combined_view (as complex128):
[[1.5e-323+2.0e-323j]
 [1.5e-323+2.0e-323j]
 [9.9e-324+1.5e-323j]
 [9.9e-324+1.5e-323j]
 [4.9e-324+9.9e-324j]
 [4.9e-324+9.9e-324j]]

idx_pos unique()
IntervalIndex([(3, 4], (2, 3], (1, 2]], dtype='interval[int64, right]')
-------------------------------------------------------------------
IntervalIndex([(-4, -3], (-4, -3], (-3, -2], (-3, -2], (-2, -1], (-2, -1]], dtype='interval[int64, right]')

Combined (ia._combined):
[[-4 -3]
 [-4 -3]
 [-3 -2]
 [-3 -2]
 [-2 -1]
 [-2 -1]]

combined_view (as complex128):
[[nan+nanj]
 [nan+nanj]
 [nan+nanj]
 [nan+nanj]
 [nan+nanj]
 [nan+nanj]]

idx_neg unique()
IntervalIndex([(-4, -3]], dtype='interval[int64, right]')
```

### Comment 2 ([user]):

Thanks for the report. Confirmed on main. Further investigations and PRs to fix are welcome.

### Comment 3 ([user]):

[user] [user] can you please re-review this [PR]((withheld: the upstream fix is not part of the task)) and let me know if any changes are required.

### Comment 4 ([user]):

Anything that can be done to get this merged?

## PR Review Comments

**[user]** on `pandas/core/arrays/interval.py`:

how does this happen? why does casting to contiguous change c16 to object?

**[user]** on `pandas/core/arrays/interval.py`:

i suspect unique will just cast this to object?

**[user]** on `pandas/core/arrays/interval.py`:

Could you use this solution instead? https://github.com/numpy/numpy/issues/16039

Also I would raise an issue in NumPy to see if taking a `.view("complex128")` of negative integers should result in nans

**[user]** on `pandas/core/arrays/interval.py`:

The reason I kept this is because [this test](https://github.com/pandas-dev/pandas/blob/e72c8a1e0ad421c1b8a7b918d995f24bed595cc3/pandas/tests/series/methods/test_unique.py#L62) was failing with the new approach.

**[user]** on `pandas/core/arrays/interval.py`:

is the hstack really necessary here since the next 2 lines is just splitting them back up?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
