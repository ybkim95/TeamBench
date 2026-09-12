# GH870_pandas_64791: BUG: Fix float16 overflow in nanmean/nansum by upcasting to float64 — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pandas-dev/pandas/issues/43929
- Repo: https://github.com/pandas-dev/pandas

## Issue Description

### 

- [X] I have checked that this issue has not already been reported.

- [X] I have confirmed this bug exists on the [latest version](https://pandas.pydata.org/docs/whatsnew/index.html) of pandas.

- [ ] I have confirmed this bug exists on the master branch of pandas.


### Reproducible Example

```python
>>> import pandas as pd
>>> df = pd.DataFrame([60000.0, 60000.0], dtype="float16")
```


```Python
/Users/username/opt/miniconda3/lib/python3.7/site-packages/numpy/core/_methods.py:47: RuntimeWarning: overflow encountered in reduce
  return umr_sum(a, axis, dtype, out, keepdims, initial, where)
0    inf
dtype: float16
```


### Issue Description

I have read the source code of pandas recently, it seems that when pandas implement DataFrame.mean() method, it calculate the tot = elements.sum() first, and then divide by the count_of_elements secondly to get the mean_value. This could cause a overflow error even if the result shouldn't be a number out of dtype range.

### Expected Behavior

1. The example should return 60000.0
2. For any Float dtype Series/DataFrame, the mean method should work and do not overflow.

### Installed Versions

<details>

INSTALLED VERSIONS
------------------
commit           : 73c68257545b5f8530b7044f56647bd2db92e2ba
python           : 3.7.6.final.0
python-bits      : 64
OS               : Darwin
OS-release       : 18.7.0
Version          : Darwin Kernel Version 18.7.0: Tue Jun 22 19:37:08 PDT 2021; root:xnu-4903.278.70~1/RELEASE_X86_64
machine          : x86_64
processor        : i386
byteorder        : little
LC_ALL           : None
LANG             : None
LOCALE           : None.UTF-8

pandas           : 1.3.3
numpy            : 1.19.2
pytz             : 2021.1
dateutil         : 2.8.1
pip              : 20.0.2
setuptools       : 45.2.0.post20200210
Cython           : 0.29.22
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
jinja2           : 2.11.3
IPython          : 7.21.0
pandas_datareader: None
bs4              : 4.9.3
bottleneck       : None
fsspec           : None
fastparquet      : None
gcsfs            : None
matplotlib       : None
numexpr          : None
odfpy            : None
openpyxl         : None
pandas_gbq       : None
pyarrow          : 3.0.0
pyxlsb           : None
s3fs             : None
scipy            : 1.6.2
sqlalchemy       : None
tables           : None
tabulate         : 0.8.9
xarray           : None
xlrd             : None
xlwt             : None
numba            : 0.53.1

</details>

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

By the way, this issue may be related with this one. 
(withheld: the upstream fix is not part of the task)

### Comment 2 ([user]):

The origin implementation nanmean is:
```Python
def nanmean(
    values: np.ndarray,
    *,
    axis: int | None = None,
    skipna: bool = True,
    mask: npt.NDArray[np.bool_] | None = None,
) -> float:
    values, mask, dtype, dtype_max, _ = _get_values(
        values, skipna, fill_value=0, mask=mask
    )
    dtype_sum = dtype_max
    dtype_count = np.dtype(np.float64)

    # not using needs_i8_conversion because that includes period
    if dtype.kind in ["m", "M"]:
        dtype_sum = np.dtype(np.float64)
    elif is_integer_dtype(dtype):
        dtype_sum = np.dtype(np.float64)
    elif is_float_dtype(dtype):
        dtype_sum = dtype
        dtype_count = dtype

    count = _get_counts(values.shape, mask, axis, dtype=dtype_count)
    the_sum = _ensure_numeric(values.sum(axis, dtype=dtype_sum))

    if axis is not None and getattr(the_sum, "ndim", False):
        count = cast(np.ndarray, count)
        with np.errstate(all="ignore"):
            # suppress division by zero warnings
            the_mean = the_sum / count
        ct_mask = count == 0
        if ct_mask.any():
            the_mean[ct_mask] = np.nan
    else:
        the_mean = the_sum / count if count > 0 else np.nan

    return the_mean
```
The overflow issue is caused by the line `the_sum = _ensure_numeric(values.sum(axis, dtype=dtype_sum))`

Suggest to implement the mean method this way:
mean of [1, 2, 3] should be 1/3 + 2/3 + 3/3 = 2.0
but not (1 + 2 + 3) / 3 = 2.0

Then there won't be an overflow problem. Below is an example code:

```Python
def nanmean(df, skip_na=False):
    result = df.values.mean()
    if skip_na:
        return result * (n_elemens / n_non_missing_values)
    return result
```

### Comment 3 ([user]):

I am having a similar issue that broke the mean average functionality. 

![image](https://user-images.githubusercontent.com/3149083/136617800-9014378e-44b8-48ae-81a8-2b361ef57772.png)
![image](https://user-images.githubusercontent.com/3149083/136618114-dea7ffc1-94ab-4882-9bc7-06cecd910ceb.png)

### Comment 4 ([user]):

we have almost 0 support for float16

if u what it then need the community to step up and put up PRs

### Comment 5 ([user]):

> we have almost 0 support for float16
> 
> if u what it then need the community to step up and put up PRs

[user] Thanks for your reply, but this is not a special case for float16. Float32 or even float64 can also have the same issue if the data volume is big enough. For instance,

```Python
>>> df = pd.DataFrame([10**38] * 100, dtype='Float32')
>>> df.mean()
```

```Python
/Users/username/miniconda3/lib/python3.6/site-packages/numpy/core/_methods.py:36: RuntimeWarning: overflow encountered in reduce
  return umr_sum(a, axis, dtype, out, keepdims, initial)
0    inf
dtype: float32
```

I can put a PR if you guys believe this makes sense.

### Comment 6 ([user]):

I'd be inclined to match `numpy` behavior here - which faces the same overflow for `float32` and `float64` (seems like `float16` is explicitly upcasted, avoiding the overflow in that case). For example,

```
info = np.finfo(np.float32)
max_v = info.max

print(np.mean([max_v, max_v], dtype="float32"))
```

gives a `RuntimeWarning` and returns `inf`. Overflow occurs because `numpy` also uses `sum` internally for `mean` - guessing because division is slow, so dividing on each step instead of once at the end would be a big perf hit.

### Comment 7 ([user]):

Thanks [user] , I tried `numpy` with `float16`, but didn't realize that `numpy.mean` will overflow when using `float32 ` and `float64`.
I tested the performance as below, and the runtime is almost 2.4x.
```Python
import numpy as np
arr = np.array(range(100000))

%timeit (arr / 100000).sum()  ##  226 µs ± 1.43 µs per loop (mean ± std. dev. of 7 runs, 1000 loops each)

%timeit arr.mean()  ## 90.9 µs ± 510 ns per loop (mean ± std. dev. of 7 runs, 10000 loops each)  
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
