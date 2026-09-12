# GH871_pandas_64755: BUG: raise on uint64 overflow in to_datetime and to_timedelta — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pandas-dev/pandas/issues/60677
- Repo: https://github.com/pandas-dev/pandas

## Issue Description

### Pandas version checks

- [X] I have checked that this issue has not already been reported.

- [X] I have confirmed this bug exists on the [latest version](https://pandas.pydata.org/docs/whatsnew/index.html) of pandas.

- [ ] I have confirmed this bug exists on the [main branch](https://pandas.pydata.org/docs/dev/getting_started/install.html#installing-the-development-version-of-pandas) of pandas.


### Reproducible Example

```python
import numpy as np
import pandas as pd
uint64_max = np.iinfo("uint64").max

try:
    dtime = pd.to_datetime(uint64_max, unit="ns")
    print("Wrong:", dtime)
    dtime = pd.to_datetime([uint64_max], unit="ns")
except Exception as err:
    print(err)

Wrong: 1969-12-31 23:59:59.999999999
cannot convert input 18446744073709551615 with the unit 'ns', at position 0
```


### Issue Description

Trying to convert out of bounds input does not raise for scalar input.

### Expected Behavior

Should raise.

### Installed Versions

<details>

INSTALLED VERSIONS
------------------
commit                : 0691c5cf90477d3503834d983f69350f250a6ff7
python                : 3.12.4
python-bits           : 64
OS                    : Linux
OS-release            : 5.14.21-150500.55.83-default
Version               : #1 SMP PREEMPT_DYNAMIC Wed Oct 2 08:09:07 UTC 2024 (0d53847)
machine               : x86_64
processor             : x86_64
byteorder             : little
LC_ALL                : None
LANG                  : de_DE.UTF-8
LOCALE                : de_DE.UTF-8

pandas                : 2.2.3
numpy                 : 2.2.1
pytz                  : 2024.1
dateutil              : 2.9.0
pip                   : 24.0
Cython                : None
sphinx                : 8.1.0
IPython               : 8.25.0
adbc-driver-postgresql: None
adbc-driver-sqlite    : None
bs4                   : 4.12.3
blosc                 : None
bottleneck            : 1.4.0
dataframe-api-compat  : None
fastparquet           : None
fsspec                : 2024.6.1
html5lib              : None
hypothesis            : 6.114.1
gcsfs                 : None
jinja2                : 3.1.4
lxml.etree            : 5.2.2
matplotlib            : 3.10.0
numba                 : None
numexpr               : None
odfpy                 : None
openpyxl              : None
pandas_gbq            : None
psycopg2              : None
pymysql               : None
pyarrow               : 17.0.0
pyreadstat            : None
pytest                : 8.2.2
python-calamine       : None
pyxlsb                : None
s3fs                  : 2024.6.1
scipy                 : 1.14.0
sqlalchemy            : None
tables                : None
tabulate              : 0.9.0
xarray                : 2025.1.1.dev3+g251329e3
xlrd                  : None
xlsxwriter            : None
zstandard             : 0.22.0
tzdata                : 2024.1
qtpy                  : None
pyqt5                 : None
</details>

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Thanks for the report! Confirmed on main, further investigations and PRs to fix are welcome!

### Comment 2 ([user]):

I've narrowed down the source of the issue. 

First, the reason these two cases behave different is that:
- the scalar `uint64_max` gets converted to `np.array([uint64_max])` (which infers `dtype='uint64'`)
- the list `[uint64_max]` get converted to `np.array([uint64_max], dtype='O')`

You can confirm this by passing either of the converted forms directly into `pd.to_datetime`

Then there is special handling for int/uint/float np.arrays in `pandas/core/tools/datetimes.py` `_to_datetime_with_unit()`:

```python
        if arg.dtype.kind in "iu":
            # Note we can't do "f" here because that could induce unwanted
            #  rounding GH#14156, GH#20445
            arr = arg.astype(f"datetime64[{unit}]", copy=False) # <---- LINE 1
            try:
                arr = astype_overflowsafe(arr, np.dtype("M8[ns]"), copy=False) # <---- LINE 2 
            except OutOfBoundsDatetime:
                if errors == "raise":
                    raise
                arg = arg.astype(object)
                return _to_datetime_with_unit(arg, unit, name, utc, errors)
            tz_parsed = None
```

Line 2 correctly handles overflow between different datetime formats (e.g. `ns` to `s`) but at this stage Line 1 has already converted from `uint64` to `datetime64[ns]` with uncaught overflow.

### Comment 3 ([user]):

take

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
