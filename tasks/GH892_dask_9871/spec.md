# GH892_dask_9871: Fix serialization bug in `BroadcastJoinLayer` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/dask/dask/issues/9870
- Repo: https://github.com/dask/dask

## Issue Description

<!-- Please include a self-contained copy-pastable example that generates the issue if possible.

Please be concise with code posted. See guidelines below on how to provide a good bug report:

- Craft Minimal Bug Reports http://matthewrocklin.com/blog/work/2018/02/28/minimal-bug-reports
- Minimal Complete Verifiable Examples https://stackoverflow.com/help/mcve

Bug reports that follow these guidelines are easier to diagnose, and so are often handled much more quickly.
-->

**Describe the issue**:

The broadcast merge codepath for dataframes throws an error when passing a list of columns in the `on` argument with a `keyError`

**Minimal Complete Verifiable Example**:

```python
import pandas as pd
import numpy as np
from dask import dataframe as dd
from distributed import Client, wait
c = Client()

df1 = pd.DataFrame({"a":np.arange(20),"b":np.arange(20),"c":[1,2]*10})
df2 = df1.copy(deep=True)
df1 = dd.from_pandas(df1,2)
df2 = dd.from_pandas(df2,5)

len(df1.merge(df2,on=["a"], how="inner", shuffle="tasks", broadcast=True))
# KeyError: "('a',)"
# Works with on="a"
```

**Anything else we need to know?**:
Same issue persists when joining on multiple columns

**Environment**:

- Dask version: 2022.12.0
- Python version: 3.9
- Operating System: ubuntu18.04
- Install method (conda, pip, source): pip

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I can confirm and can reproduce this. My best guess is that this is a serialization error or we're calling a stringify or smth too eagerly.

basically the list is cast to a tuple and then stringified somewhere, i.e. `["a"]` becomes `"('a',)"`. Passing a tuple directly or the literal works as expected.

If I had to guess, [this](https://github.com/dask/dask/blob/96a72df0aeb4a7d04844e1ebc2fddb30265a0bc7/dask/layers.py#L889-L892) looks suspicious but I don't fully understand what's going on there. Maybe [user] ?

### Comment 2 ([user]):

Thanks for raising [user] ! I ran into this bug yesterday, but didn't get a chance to raise and issue and investigate yet. [user] is correct that this is likely another HLG-serialization edge case (probably having to do with msgpack not distinguishing lists/tuples). I will try to figure out a fix, but also look forward to something like (withheld: the upstream fix is not part of the task) avoiding these problems altogether :)

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
