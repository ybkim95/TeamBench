# GH869_pandas_64806: BUG: fix DatetimeIndex + DateOffset near DST transitions — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pandas-dev/pandas/issues/28610
- Repo: https://github.com/pandas-dev/pandas

## Issue Description

#### Code Sample, a copy-pastable example if possible

```python
>>> import pandas as pd
>>> idx = pd.DatetimeIndex(['2000-03-26 04:00'], tz='Europe/Berlin')  # Switch to DST was on that day
>>> idx
DatetimeIndex(['2000-03-26 04:00:00+02:00'], dtype='datetime64[ns, Europe/Berlin]', freq=None)
>>> idx + pd.DateOffset(hours=-2)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/var/local/conda/envs/pandas-debug/lib/python3.7/site-packages/pandas/core/indexes/datetimelike.py", line 510, in __add__
    result = self._data.__add__(maybe_unwrap_index(other))
  File "/var/local/conda/envs/pandas-debug/lib/python3.7/site-packages/pandas/core/arrays/datetimelike.py", line 1212, in __add__
    result = self._add_offset(other)
  File "/var/local/conda/envs/pandas-debug/lib/python3.7/site-packages/pandas/core/arrays/datetimes.py", line 832, in _add_offset
    result = result.tz_localize(self.tz)
  File "/var/local/conda/envs/pandas-debug/lib/python3.7/site-packages/pandas/core/arrays/datetimes.py", line 1151, in tz_localize
    self.asi8, tz, ambiguous=ambiguous, nonexistent=nonexistent
  File "pandas/_libs/tslibs/tzconversion.pyx", line 276, in pandas._libs.tslibs.tzconversion.tz_localize_to_utc
pytz.exceptions.NonExistentTimeError: 2000-03-26 02:00:00
>>> idx[0] + pd.DateOffset(hours=-2)
Timestamp('2000-03-26 01:00:00+0100', tz='Europe/Berlin')
```
#### Problem description

The vectorized operation `DatetimeIndex + DateOffset` is broken around the DST switching time. However, the same operation works element-wise (`Timestamp + DateOffset`), so I would expect either both versions to work (preferably) or both versions to fail with the same error.

#### Expected Output

```python
DatetimeIndex(['2000-03-26 01:00:00+01:00'], dtype='datetime64[ns, Europe/Berlin]', freq=None)
```

#### Output of ``pd.show_versions()``

<details>

INSTALLED VERSIONS
------------------
commit           : None
python           : 3.7.4.final.0
python-bits      : 64
OS               : Linux
OS-release       : 5.0.0-29-generic
machine          : x86_64
processor        : x86_64
byteorder        : little
LC_ALL           : None
LANG             : en_US.UTF-8
LOCALE           : en_US.UTF-8

pandas           : 0.25.1
numpy            : 1.16.5
pytz             : 2019.2
dateutil         : 2.8.0
pip              : 19.2.3
setuptools       : 41.2.0
Cython           : None
pytest           : None
hypothesis       : None
sphinx           : None
blosc            : None
feather          : None
xlsxwriter       : None
lxml.etree       : None
html5lib         : None
pymysql          : None
psycopg2         : None
jinja2           : None
IPython          : None
pandas_datareader: None
bs4              : None
bottleneck       : None
fastparquet      : None
gcsfs            : None
lxml.etree       : None
matplotlib       : None
numexpr          : None
odfpy            : None
openpyxl         : None
pandas_gbq       : None
pyarrow          : None
pytables         : None
s3fs             : None
scipy            : None
sqlalchemy       : None
tables           : None
xarray           : None
xlrd             : None
xlwt             : None
xlsxwriter       : None

</details>

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

The issue is in this line: https://github.com/pandas-dev/pandas/blob/83eb75bf04e9020a13b1109ac714207159d7c11a/pandas/core/arrays/datetimes.py#L830

`tz_localize` has keyword argument `ambiguous` and `nonexistent` arguments to handle these cases.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
