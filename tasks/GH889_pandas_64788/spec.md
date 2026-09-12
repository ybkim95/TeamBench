# GH889_pandas_64788: BUG: fix date_range inclusive filtering with periods — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pandas-dev/pandas/issues/46331
- Repo: https://github.com/pandas-dev/pandas

## Issue Description

### Pandas version checks

- [X] I have checked that this issue has not already been reported.

- [X] I have confirmed this bug exists on the [latest version](https://pandas.pydata.org/docs/whatsnew/index.html) of pandas.

- [x] I have confirmed this bug exists on the main branch of pandas.


### Reproducible Example

```python
import pandas as pd

pd.date_range(start='2020-06-01', periods=4, inclusive='both')
# DatetimeIndex(['2020-06-01', '2020-06-02', '2020-06-03', '2020-06-04'], dtype='datetime64[ns]', freq='D')

pd.date_range(start='2020-06-01', periods=4, inclusive='neither')
# Output:
# DatetimeIndex(['2020-06-02', '2020-06-03', '2020-06-04'], dtype='datetime64[ns]', freq='D')
# Expected:
# DatetimeIndex(['2020-06-02', '2020-06-03'], dtype='datetime64[ns]', freq='D')

pd.date_range(start='2020-06-01', periods=4, inclusive='left')
# Output:
# DatetimeIndex(['2020-06-01', '2020-06-02', '2020-06-03', '2020-06-04'], dtype='datetime64[ns]', freq='D')
# Expected:
# DatetimeIndex(['2020-06-01', '2020-06-02', '2020-06-03'], dtype='datetime64[ns]', freq='D')

pd.date_range(start='2020-06-01', periods=4, inclusive='right')
# DatetimeIndex(['2020-06-02', '2020-06-03', '2020-06-04'], dtype='datetime64[ns]', freq='D')
```


### Issue Description

# First of all, I have no idea if it actually a bug, maybe it not understood for me.

## How do I think the function should bring the output:
## Calculate with inclusive=True and then filter out left/right/both at the edges.

### Expected Behavior

```
pd.date_range(start='2020-06-01', periods=4, inclusive='neither')

# Output:
DatetimeIndex(['2020-06-02', '2020-06-03', '2020-06-04'], dtype='datetime64[ns]', freq='D')

# Expected:
DatetimeIndex(['2020-06-02', '2020-06-03'], dtype='datetime64[ns]', freq='D')
```
```
pd.date_range(start='2020-06-01', periods=4, inclusive='left')

# Output:
DatetimeIndex(['2020-06-01', '2020-06-02', '2020-06-03', '2020-06-04'], dtype='datetime64[ns]', freq='D')

# Expected:
DatetimeIndex(['2020-06-01', '2020-06-02', '2020-06-03'], dtype='datetime64[ns]', freq='D')
```

### Installed Versions

<details>

INSTALLED VERSIONS
------------------
commit           : 06d230151e6f18fdb8139d09abf539867a8cd481
python           : 3.9.10.final.0
python-bits      : 64
OS               : Linux
OS-release       : 5.13.0-30-generic
Version          : #33-Ubuntu SMP Fri Feb 4 17:03:31 UTC 2022
machine          : x86_64
processor        : x86_64
byteorder        : little
LC_ALL           : None
LANG             : en_IL
LOCALE           : en_IL.UTF-8

pandas           : 1.4.1
numpy            : 1.22.2
pytz             : 2021.3
dateutil         : 2.8.2
pip              : 22.0.3
setuptools       : 59.8.0
Cython           : None
pytest           : None
hypothesis       : None
sphinx           : 4.4.0
blosc            : None
feather          : None
xlsxwriter       : None
lxml.etree       : 4.8.0
html5lib         : None
pymysql          : None
psycopg2         : 2.9.3
jinja2           : 3.0.3
IPython          : 7.32.0
pandas_datareader: None
bs4              : None
bottleneck       : None
fastparquet      : None
fsspec           : 2022.02.0
gcsfs            : None
matplotlib       : 3.5.1
numba            : None
numexpr          : None
odfpy            : None
openpyxl         : None
pandas_gbq       : None
pyarrow          : None
pyreadstat       : None
pyxlsb           : None
s3fs             : 2022.02.0
scipy            : 1.8.0
sqlalchemy       : 1.4.31
tables           : None
tabulate         : None
xarray           : None
xlrd             : None
xlwt             : None
zstandard        : None

</details>

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I agree with you that this does not appear consistent, even with my comment below.

Interestingly, it rather throws up an odd nomenclature item. Is a `period` defined as that between two timepoints or as a single time point, i.e. is [time1, time2, time3] two periods or three? It seems that pandas has adopted the three periods definition and as such that probably wont be changed but the inclusive arg should work properly I think. This might break a lot of tests though.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
