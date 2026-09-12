# GH978_pandas_64846: Revert "BUG: distinguish bool from int in object-dtype hash table" — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pandas-dev/pandas/issues/64749
- Repo: https://github.com/pandas-dev/pandas

## Issue Description

### Pandas version checks

- [x] I have checked that this issue has not already been reported.

- [x] I have confirmed this bug exists on the [latest version](https://pandas.pydata.org/docs/whatsnew/index.html) of pandas.

- [x] I have confirmed this bug exists on the [main branch](https://pandas.pydata.org/docs/dev/getting_started/install.html#installing-the-development-version-of-pandas) of pandas.


### Reproducible Example

```python
import pandas as pd

df = pd.DataFrame({True: [4, 5]})
print(df[True])
s = pd.Series([7, 8], name='_tmp')
df = pd.concat([df[True], s], axis=1)
print(df[True])
```

### Issue Description

In the latest release, and up until a few days ago with the nightlies, this passed

Now:
```python-traceback
0    4
1    5
Name: True, dtype: int64
Traceback (most recent call last):
  File "/home/marcogorelli/polars-api-compat-dev/.venv/lib/python3.13/site-packages/pandas/core/indexes/base.py", line 3710, in get_loc
    return self._engine.get_loc(casted_key)
           ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
  File "pandas/_libs/index.pyx", line 172, in pandas._libs.index.IndexEngine.get_loc
  File "pandas/_libs/index.pyx", line 201, in pandas._libs.index.IndexEngine.get_loc
  File "pandas/_libs/hashtable_class_helper.pxi", line 7697, in pandas._libs.hashtable.PyObjectHashTable.get_item
  File "pandas/_libs/hashtable_class_helper.pxi", line 7705, in pandas._libs.hashtable.PyObjectHashTable.get_item
KeyError: True

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/marcogorelli/polars-api-compat-dev/g.py", line 7, in <module>
    print(df[True])
          ~~^^^^^^
  File "/home/marcogorelli/polars-api-compat-dev/.venv/lib/python3.13/site-packages/pandas/core/frame.py", line 4234, in __getitem__
    indexer = self.columns.get_loc(key)
  File "/home/marcogorelli/polars-api-compat-dev/.venv/lib/python3.13/site-packages/pandas/core/indexes/base.py", line 3717, in get_loc
    raise KeyError(key) from err
KeyError: True
```

### Expected Behavior

```
0    4
1    5
Name: True, dtype: int64
0    4
1    5
Name: True, dtype: int64
```

### Installed Versions

<details>

INSTALLED VERSIONS
------------------
commit                : 497fe85391793659986641261ad25df0e7fa6b4b
python                : 3.13.9
python-bits           : 64
OS                    : Linux
OS-release            : 6.6.87.2-microsoft-standard-WSL2
Version               : #1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025
machine               : x86_64
processor             : x86_64
byteorder             : little
LC_ALL                : None
LANG                  : C.UTF-8
LOCALE                : C.UTF-8

pandas                : 3.1.0.dev0+437.g497fe85391
numpy                 : 2.5.0.dev0+git20260316.80bcb8b
dateutil              : 2.9.0.post0
pip                   : 26.0.1
Cython                : None
sphinx                : None
IPython               : 9.11.0
adbc-driver-postgresql: None
adbc-driver-sqlite    : None
bs4                   : None
bottleneck            : None
fastparquet           : None
fsspec                : 2026.2.0
html5lib              : None
hypothesis            : 6.151.9
gcsfs                 : None
jinja2                : None
lxml.etree            : None
matplotlib            : None
numba                 : None
numexpr               : None
odfpy                 : None
openpyxl              : None
psycopg2              : None
pymysql               : None
pyarrow               : 23.0.1
pyiceberg             : None
pyreadstat            : None
pytest                : 9.0.2
python-calamine       : None
pytz                  : None
pyxlsb                : None
s3fs                  : None
scipy                 : None
sqlalchemy            : None
tables                : None
tabulate              : None
xarray                : None
xlrd                  : None
xlsxwriter            : None
zstandard             : None
qtpy                  : None
pyqt5                 : None

</details>

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

The regression was introduced by #64639 (BUG: distinguish bool from int in object-dtype hash table).

The fix in `khash_python.h` added a check `PyBool_Check(a) != PyBool_Check(b)` to distinguish bool from int. However, `np.True_` is a numpy bool scalar, not a Python bool, so `PyBool_Check(np.True_)` returns 0. This means `True` (Python bool) and `np.True_` (numpy bool) are now treated as different keys, breaking lookups where a column was created with `np.True_` but accessed with `True`.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
