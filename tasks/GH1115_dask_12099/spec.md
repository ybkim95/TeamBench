# GH1115_dask_12099: Address collection-based ``meta`` arguments in ``GroupByApply`` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/dask/dask/issues/11990
- Repo: https://github.com/dask/dask

## Issue Description

**Describe the issue**:

For LocalCluster the following assertion error appears that isn't self descriptive. I have faced this issue few times. 
```
Traceback (most recent call last):
  File "/home/dmitrybalabka/src/test_cli.py", line 42, in <module>
    test_filter_first_empty_rows_basic()
  File "/home/dmitrybalabka/src/test_cli.py", line 38, in test_filter_first_empty_rows_basic
    result_ddf.compute().sort_values(['ID', 'time']).reset_index(drop=True)
    ^^^^^^^^^^^^^^^^^^^^
  File "/home/dmitrybalabka/src/.venv/lib/python3.11/site-packages/dask_expr/_collection.py", line 479, in compute
    out = out.optimize(fuse=fuse)
          ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dmitrybalabka/src/.venv/lib/python3.11/site-packages/dask_expr/_collection.py", line 594, in optimize
    return new_collection(self.expr.optimize(fuse=fuse))
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dmitrybalabka/src/.venv/lib/python3.11/site-packages/dask_expr/_expr.py", line 93, in optimize
    return optimize(self, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dmitrybalabka/src/.venv/lib/python3.11/site-packages/dask_expr/_expr.py", line 3118, in optimize
    return optimize_until(expr, stage)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dmitrybalabka/src/.venv/lib/python3.11/site-packages/dask_expr/_expr.py", line 3089, in optimize_until
    expr = optimize_blockwise_fusion(expr)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/dmitrybalabka/src/.venv/lib/python3.11/site-packages/dask_expr/_expr.py", line 3286, in optimize_blockwise_fusion
    expr, done = _fusion_pass(expr)
                 ^^^^^^^^^^^^^^^^^^
  File "/home/dmitrybalabka/src/.venv/lib/python3.11/site-packages/dask_expr/_expr.py", line 3251, in _fusion_pass
    dep.npartitions == root.npartitions or next._broadcast_dep(dep)
    ^^^^^^^^^^^^^^^
  File "/home/dmitrybalabka/src/.venv/lib/python3.11/site-packages/dask_expr/_expr.py", line 397, in npartitions
    return len(self.divisions) - 1
               ^^^^^^^^^^^^^^
  File "/home/dmitrybalabka/.pyenv/versions/3.11.7/lib/python3.11/functools.py", line 1001, in __get__
    val = self.func(instance)
          ^^^^^^^^^^^^^^^^^^^
  File "/home/dmitrybalabka/src/.venv/lib/python3.11/site-packages/dask_expr/_expr.py", line 381, in divisions
    return tuple(self._divisions())
                 ^^^^^^^^^^^^^^^^^
  File "/home/dmitrybalabka/src/venv/lib/python3.11/site-packages/dask_expr/_expr.py", line 529, in _divisions
    assert arg.divisions == dependencies[0].divisions
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
```

**Minimal Complete Verifiable Example**:

```shell
python test.py
```
```python
import numpy as np
import dask.dataframe as dd
import pandas as pd
from datetime import datetime

def filter_first_empty_rows(
    data: dd.DataFrame,
    col: str,
    time_col: str,
    id_col: str,
    train_till: datetime,
) -> dd.DataFrame:
    
    def _filter_group(df: pd.DataFrame) -> pd.DataFrame:
        first_date = df.loc[~df[col].isna(), time_col].min()
        mask = (df[time_col] >= first_date) | (df[time_col] > train_till)
        return df[mask]

    return data.groupby(id_col, group_keys=False).apply(_filter_group, meta=data).reset_index(drop=True)


def test_filter_first_empty_rows_basic():
    # Create a dataframe with two IDs:
    # For ID 1: first non-null price is on 2021-01-02, so any row before that should be dropped;
    # For ID 2: all price values are NaN so only rows after train_till are kept.
    data = pd.DataFrame({
        'ID': [1, 1, 1, 2, 2, 2],
        'time': pd.to_datetime([
            '2021-01-01', '2021-01-02', '2021-01-03',
            '2021-01-01', '2021-01-02', '2021-01-03'
        ]),
        'price': [np.nan, 100, np.nan, np.nan, np.nan, np.nan]
    })
    ddf = dd.from_pandas(data, npartitions=1)
    train_till = datetime(2021, 1, 2)
    
    result_ddf = filter_first_empty_rows(ddf, 'price', 'time', 'ID', train_till)
    result_ddf.compute().sort_values(['ID', 'time']).reset_index(drop=True)
    

if __name__ == "__main__":
    test_filter_first_empty_rows_basic()
    print("Test passed!")
```

**Environment**:

- Dask version: 2024.12.1
- Python version: 3.11
- Operating System: WSL
- Install method (conda, pip, source): poetry

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

The issue is quiet silly. If I pass `meta` param in `apply()` function as following `meta=data._meta` instead of `meta=data` problem dissapears:
```
return data.groupby(id_col, group_keys=False).apply(_filter_group, meta=data._meta).reset_index(drop=True)
```

### Comment 2 ([user]):

> The issue is quiet silly. If I pass `meta` param in `apply()` function as following `meta=data._meta` instead of `meta=data` problem dissapears:
> 
> ```
> return data.groupby(id_col, group_keys=False).apply(_filter_group, meta=data._meta).reset_index(drop=True)
> ```

I encountered this same issue today while creating a toy example. Can confirm `data._meta` fixes the problem.

### Comment 3 ([user]):

At the very least we should add a string to the assertion to explain what has happened.

```python
assert arg.divisions == dependencies[0].divisions, "Detailed error string"
```

But maybe we need to look into setting the meta correctly.

[user] do you have some time to look at this?

### Comment 4 ([user]):

>[user] do you have some time to look at this?

I submitted (withheld: the upstream fix is not part of the task) to address this particular case. I didn't have time to work through a more-general fix yet, but the updated assertion should help if we run into the problem in other places.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
