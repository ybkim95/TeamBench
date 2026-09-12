# GH928_dask_9646: Fix groupby-aggregation when grouping on an index by name — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/dask/dask/issues/9643
- Repo: https://github.com/dask/dask

## Issue Description

**Describe the issue**:
As pointed out in [this comment]((withheld: the upstream fix is not part of the task)#issuecomment-1310001867) (thanks [user] !), the changes in  [9442]((withheld: the upstream fix is not part of the task)) do not properly handle the case that we are grouping on the index by name.

**Minimal Complete Verifiable Example**:

```python
import pandas as pd
import dask.dataframe as dd

pdf = pd.DataFrame(
    {"a": [1, 2, 3, 4, 5, 6, 7, 8, 9], "b": [4, 5, 6, 3, 2, 1, 0, 0, 0]},
    index=[0, 1, 3, 5, 6, 8, 9, 9, 9],
)
ddf = dd.from_pandas(pdf, npartitions=3)

ddf2 = ddf.set_index("a")
ddf2.groupby("a").agg({"b": "mean"})
```

Result: `KeyError: "['a'] not in index"`

## PR Review Comments

**[user]** on `dask/dataframe/tests/test_groupby.py`:

This passes on `main` -- is this maybe supposed to use `ddf2`?

**[user]** on `dask/dataframe/groupby.py`:

Is it possible for `list(column_projection.intersection(self.obj.columns))` to ever be empty when `column_projection` isn't empty? If so, should this be `if list(column_projection.intersection(self.obj.columns))` instead?

**[user]** on `dask/dataframe/tests/test_groupby.py`:

Oops - good catch!

**[user]** on `dask/dataframe/groupby.py`:

I moved the intersection logic into the `column_projection` calculation itself (above). However, I suppose we would techincally still want to use the `getitem` operation when `column_projection` is empty, because this means the aggregation only needs columns that are part of the index. Not sure if this is a valid scenario, so I agree that avoiding the `getitem` when `column_projection` is empty seems safer for now.

**[user]** on `dask/dataframe/tests/test_groupby.py`:

Not meant as a blocking comment for this PR: I know we're using this check elsewhere to mean "we're doing column projection", but it feels somewhat indirect / brittle to me. For instance,`hlg_layer(agg.dask, "getitem")` means that there's _a_ `getitem` layer in the graph, but it could still pass even if we weren't getting column projection. Are there other things we can do that are a more direct check that we did not attempt to load in specific columns?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
