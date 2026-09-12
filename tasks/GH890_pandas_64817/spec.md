# GH890_pandas_64817: BUG: fix KeyError when looking up tuple in object Index with duplicates — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pandas-dev/pandas/issues/37800
- Repo: https://github.com/pandas-dev/pandas

## Issue Description

E.g.

```
s = pd.Series([1, 1], index=[(1, 1), (1, 1)])
s[(1, 1)]
```

raises `KeyError: (1, 1)`. Within `pandas._libs.index.IndexEngine._get_loc_duplicates`, we're using ndarray.searchsorted which interprets the tuple as an array-like of values to search for rather than a single tuple.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Similar problems with loc. Index does not have to be non-unique there

```
s = pd.Series([1, 1], index=[(1, 2), (1, 1)])

s.loc[(1, 2)]
```

```
pandas.core.indexing.IndexingError: Too many indexers
```

Tuple support is not very good here.

### Comment 2 ([user]):

This is conflicting with the multiindex selector which uses tuple as the label for different levels.
```python
>>>s = pd.Series([1, 1], index=pd.Index([(1, 2), (1, 1)]))
>>>s.loc[(1,2)]
1
```
Ambiguous when using tuple index.

### Comment 3 ([user]):

[user] what is ambiguous? When Series has a multi-index, a tuple consists of labels for different levels. When Series doesn't have a multi-index, a tuple is a single label. Or is there some other case(s)?

### Comment 4 ([user]):

```python
>>>s = pd.Series([1,2], index=pd.Index([((1,1),1),((1,2),2)]))
>>>s.loc[(1,1)]
1    1
dtype: int64
```
When tuple index is the zero level of multiindex.

But it seems still reasonable when applying to a non-multiindex.

### Comment 5 ([user]):

Ack, I see. A similar example:

```
s = pd.Series([1, 2], index=pd.Index([((1, 1), 1), (1, 1)]))
print(s.loc[(1, 1)])
```

one might expect to get `2` rather than the actual output of `1`. In any case, oddities in the case of nested tuples should not imply that we shouldn't make improvements on supporting tuples.

## PR Review Comments

**[user]** on `pandas/_libs/index.pyx`:

Is a similar fix needed `if self.is_monotonic_decreasing`?

**[user]** on `pandas/_libs/index.pyx`:

ATM this follows the pattern used by other classes in this file. In an upcoming pass i plan to try to de-duplicate them. At that point ill look into a monotonic_decreasing fastpaths

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
