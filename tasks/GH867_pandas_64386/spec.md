# GH867_pandas_64386: BUG: fix sort_index AssertionError with RangeIndex and level parameter — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pandas-dev/pandas/issues/64383
- Repo: https://github.com/pandas-dev/pandas

## Issue Description

### Pandas version checks

- [x] I have checked that this issue has not already been reported.

- [x] I have confirmed this bug exists on the [latest version](https://pandas.pydata.org/docs/whatsnew/index.html) of pandas.

- [x] I have confirmed this bug exists on the [main branch](https://pandas.pydata.org/docs/dev/getting_started/install.html#installing-the-development-version-of-pandas) of pandas.


### Reproducible Example

```python
import pandas as pd

df = pd.DataFrame({"a": [1, 2, 3], "foo": [1, 0, 2]}).set_index(["foo"], drop=True)
print(df.sort_index(level="foo"))  # Works in pandas 2 and 3

df = pd.DataFrame({"a": [1, 2, 3], "foo": [0, 1, 2]}).set_index(["foo"], drop=True)
print(df.sort_index(level="foo"))  # Fails in pandas 3

df = pd.DataFrame({"a": [1, 2, 3]})
df.index.names = ["foo"]
print(df.sort_index(level="foo"))  # Fails in pandas 2 and 3
```

### Issue Description

From pandas-3.0.0 on the above example fails with
```
     a
foo   
0    1
1    2
2    3
Traceback (most recent call last):
  File "/tmp/indextest.py", line 8, in <module>
    print(df.sort_index(level="foo"))
          ~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/home/jmu3si/Devel/pandas/pandas/core/frame.py", line 8394, in sort_index
    return super().sort_index(
           ~~~~~~~~~~~~~~~~~~^
        axis=axis,
        ^^^^^^^^^^
    ...<7 lines>...
        key=key,
        ^^^^^^^^
    )
    ^
  File "/home/jmu3si/Devel/pandas/pandas/core/generic.py", line 5187, in sort_index
    new_data = self._mgr.take(indexer, axis=baxis, verify=False)
  File "/home/jmu3si/Devel/pandas/pandas/core/internals/managers.py", line 1069, in take
    return self.reindex_indexer(
           ~~~~~~~~~~~~~~~~~~~~^
        new_axis=new_labels,
        ^^^^^^^^^^^^^^^^^^^^
    ...<2 lines>...
        allow_dups=True,
        ^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/jmu3si/Devel/pandas/pandas/core/internals/managers.py", line 829, in reindex_indexer
    assert isinstance(indexer, np.ndarray)
           ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
AssertionError
```

The issue occurs when the following conditions are met:

* The index is a `RangeIndex`.
* There is only one index level.
* `.sort_index` is called with the `level=` argument.

It feels like kind of a regression because as it seems pandas-2.x ended up with an `Index` in some cases in which pandas-3.x ends up with a `RangeIndex`. So there are cases that worked fine in `pandas-2` which don't in pandas-3.

### Expected Behavior

Up to pandas-2.3.3 this worked and gave the expected output:
```
     a
foo   
0    2
1    1
2    3
     a
foo   
0    1
1    2
2    3
     a
foo   
0    1
1    2
2    3
```

### Installed Versions

<details>
INSTALLED VERSIONS
------------------
commit                : e04b26f375035e5106cb913e47b6db612f4ebb11
python                : 3.13.12
python-bits           : 64
OS                    : Linux
OS-release            : 6.8.0-101-generic
Version               : #101-Ubuntu SMP PREEMPT_DYNAMIC Mon Feb  9 10:15:05 UTC 2026
machine               : x86_64
processor             : x86_64
byteorder             : little
LC_ALL                : None
LANG                  : de_DE.UTF-8
LOCALE                : de_DE.UTF-8

pandas                : 3.0.1
numpy                 : 2.4.2
dateutil              : 2.9.0.post0
pip                   : None
Cython                : None
sphinx                : None
IPython               : None
adbc-driver-postgresql: None
adbc-driver-sqlite    : None
bs4                   : None
bottleneck            : None
fastparquet           : None
fsspec                : None
html5lib              : None
hypothesis            : None
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
pyarrow               : None
pyiceberg             : None
pyreadstat            : None
pytest                : None
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

its seems that when the index is RangeIndex with single level and level= is passed to sort_index, the internal indexer is not a numpy array, which cause the assertion failure in reindexer_indexer
this looks like a regression compared to pandas 2.x i had like to take this issue

### Comment 2 (@repeating):

hey, i looked into this — the issue is in `RangeIndex.sort_values` returning a `RangeIndex` as the indexer instead of an ndarray when `return_indexer=True`. the block manager asserts `isinstance(indexer, np.ndarray)` so it crashes. opening a PR with the fix.

### Comment 3 ([user]):

Hi, I was also working on a PR for this sorry for not mentioning it. If repeating's solution works, feel free to close my PR.

### Comment 4 ([user]):

Hello, I forgot to also mention that I was working on a PR. I apologize for not mentioning this. Feel free to close my PR request if it is adding repeating info.

## PR Review Comments

**[user]** on `pandas/core/indexes/range.py`:

what are the consequences of this?  knowing you have a RangeIndex can be good for performance downstream

**@repeating** on `pandas/core/indexes/range.py`:

the indexer here is only consumed by `self._mgr.take(indexer, ...)` which asserts `isinstance(indexer, np.ndarray)` — nothing downstream of `sort_values(return_indexer=True)` uses the indexer as a RangeIndex, it's purely a positional array for the block manager's take path. the base class `Index.sort_values` already returns `np.ndarray` for this, so this just brings the RangeIndex override in line with that contract.

**[user]** on `pandas/core/indexes/range.py`:

The question is, if we want to treat it as a special case for performance reasons. If we get a `RangeIndex` for sorting, all we need is to maybe reverse the `RangeIndex`. I don't think it makes sense make an `np.arange()` from the `RangeIndex`, sort that downstream and then eventually turn it back into a `RangeIndex`.

If that's what's happening.

**@repeating** on `pandas/core/indexes/range.py`:

yeah good point — the full sort_index → sortlevel → sort_values → take chain doesn't really need the take() at all when the RangeIndex is already sorted (or just needs reversing). that would be a nice optimization.

this PR is just the minimal fix to stop the crash — sort_values was returning RangeIndex as the indexer instead of np.ndarray, which violates the base class contract and blows up in _mgr.take(). converting to np.arange keeps the existing code path working correctly.

the smarter short-circuit (detecting RangeIndex in sort_index/get_indexer_indexer and skipping take entirely) would be a separate change with a broader scope. happy to look into that as a follow-up if you'd like, or keep this scoped to just the bug fix.

**[user]** on `pandas/core/indexes/range.py`:

I would actually agree on fixing the regression quickly for 3.0.2. The performance optimization then can be addressed in a follow up issue.

But that's for the core devs to decide.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
