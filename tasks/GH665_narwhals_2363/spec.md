# GH665_narwhals_2363: fix: Preserve pandas column name attribute — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/narwhals-dev/narwhals/issues/1483
- Repo: https://github.com/narwhals-dev/narwhals

## Issue Description

```python
import pandas as pd
# import narwhals.stable.v1 as nw
import narwhals as nw

df = pd.DataFrame({'a': [1,2,3], 'b': [4,5,6]})
df.columns.name = 'foo'

print(nw.from_native(df).select(c=nw.col('a')+1).to_native())
print(nw.from_native(df).with_columns(c=nw.col('a')+1).to_native())
print(nw.from_native(df).to_native())
print(nw.from_native(df).to_native().assign(c=lambda df: df['a']+1))
```

outputs
```python
   c
0  2
1  3
2  4
   a  b  c
0  1  4  2
1  2  5  3
2  3  6  4
foo  a  b
0    1  4
1    2  5
2    3  6
foo  a  b  c
0    1  4  2
1    2  5  3
2    3  6  4
```

expected:
```python
foo  c
0    2
1    3
2    4
foo  a  b  c
0    1  4  2
1    2  5  3
2    3  6  4
foo  a  b
0    1  4
1    2  5
2    3  6
foo  a  b  c
0    1  4  2
1    2  5  3
2    3  6  4
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

having said that...should we really care? is this in-scope for Narwhals? not totally sure I want to deal with multi-index columns' names weirdness

### Comment 2 ([user]):

> should we really care?

I feel slightly uncomfortable not caring about it. Some "meta" information might be easy(er) than expected to preserve. Except at the same time I totally share this take:

> not totally sure I want to deal with multi-index columns' names weirdness

and also:

> is this in-scope for Narwhals?

Probably not 😂

## PR Review Comments

**[user]** on `narwhals/_dask/dataframe.py`:

This might be one step ahead of [dask#11874](https://github.com/dask/dask/issues/11874)

**[user]** on `narwhals/_pandas_like/dataframe.py`:

Should we use `rename_axis(..., copy=False)`?

**[user]** on `narwhals/_pandas_like/namespace.py`:

Can rollback this, or compress it even more

**[user]** on `narwhals/translate.py`:

Mental sanity for symmetry with other pandas-like and order of the spec 😅

**[user]** on `tests/preserve_pandas_like_columns_name_attr_test.py`:

I wanted to concatenate two methods here, mostly for the sake of it.
Might be worth reparametrizing it

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
