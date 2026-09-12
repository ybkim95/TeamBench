# GH904_pandas_64767: BUG: MultiIndex.sortlevel raises TypeError for incomparable types — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pandas-dev/pandas/issues/21136
- Repo: https://github.com/pandas-dev/pandas

## Issue Description

#### Code Sample, a copy-pastable example if possible

```python
# Column 'a' has both Timestamps and a string
df = pd.Series([pd.Timestamp('2011/4/9'), pd.Timestamp('2010/4/9'), '2009/4/9'], dtype='object', name='a').to_frame()
df['b'] = [1,2,3]
df['c'] = [2,1,3]
df.set_index('a', inplace=True)
df.set_index('c', append=True, inplace=True)
# No TypeError
df.sort_index(level='a')
# Raises TypeError: Cannot compare type 'Timestamp' with type 'str'
df.reset_index(level='c').sort_index(level='a')

```
#### Problem description

Sorting by mixed types should (and did in 0.22) raise a TypeError. Now it looks like it does raise a TypeError if there is only a single level in the index, but does not if there is another level that you're not sorting on.

#### Output of ``pd.show_versions()``

<details>

INSTALLED VERSIONS
------------------
commit: None
python: 2.7.14.final.0
python-bits: 64
OS: Darwin
OS-release: 17.4.0
machine: x86_64
processor: i386
byteorder: little
LC_ALL: None
LANG: en_US.UTF-8
LOCALE: None.None

pandas: 0.23.0
pytest: 3.2.3
pip: 10.0.1
setuptools: 36.5.0.post20170921
Cython: 0.27.3
numpy: 1.13.3
scipy: 1.0.0
pyarrow: None
xarray: None
IPython: 5.4.1
sphinx: 1.6.4
patsy: None
dateutil: 2.7.2
pytz: 2017.3
blosc: None
bottleneck: None
tables: None
numexpr: 2.5.1
feather: None
matplotlib: 2.1.1
openpyxl: None
xlrd: 1.1.0
xlwt: None
xlsxwriter: None
lxml: None
bs4: None
html5lib: 0.9999999
sqlalchemy: 1.2.7
pymysql: None
psycopg2: 2.7.4 (dt dec pq3 ext lo64)
jinja2: 2.10
s3fs: 0.1.2
fastparquet: 0.1.5
pandas_gbq: None
pandas_datareader: None

</details>

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Thanks for the report - investigation and PRs welcome!

### Comment 2 ([user]):

It has to do with sorting via MultiIndex vs. normal Index. Internally, MultiIndexes are already sorted upon initialization. Each level gets a corresponding pd.Categorical array, which is initialized with ordered=True. Later on, the sorting is just done by looking at the already ordered categories. So the fix would either be to make pd.Categorical() fail for mixed dtype when ordered=True, or to do some sort of check when initializing MultiIndex to not call ordered=True when creating these Categorical arrays (and then keep track of the fact that its not ordered).

I don't know enough about Pandas internals to know which route is better.

In the past, it looks like an explicit argsort() call was made, but now it just looks at the already sorted categories.

## PR Review Comments

**[user]** on `pandas/core/indexes/multi.py`:

Should the monotonic check (increasing/decreasing) be dependent on `ascending`?

**[user]** on `pandas/core/indexes/multi.py`:

No, the point is just to raise on incomparable objects. we dont actually care about the argsort result

**[user]** on `pandas/core/indexes/multi.py`:

Sure but if the values are only `is_monotonic_decreasing` shouldn't we perform the same check?

**[user]** on `pandas/core/indexes/multi.py`:

good point, will update

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
