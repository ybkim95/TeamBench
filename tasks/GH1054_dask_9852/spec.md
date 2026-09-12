# GH1054_dask_9852: Satisfy `broadcast` argument in `DataFrame.merge` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/dask/dask/issues/9851
- Repo: https://github.com/dask/dask

## Issue Description

**Describe the issue**:

The `dask.dataframe.merge` API should use a broadcast-based merge when `broadcast=True`. The only exception should be when a broadcast-based algorithm is prohibited for the specified `how` and/or `shuffle` arguments. Within the current `dd.merge` implementation, the broadcast-based merge is only used when `shuffle="tasks"` is explicitly specified. My stance is that this is a bug.  

**Minimal Complete Verifiable Example**:

```python
import dask.dataframe as dd
from dask.utils_test import hlg_layer

left = dd.from_dict({"a": [1, 2] * 100, "b_left": range(200)}, npartitions=20)
right = dd.from_dict({"a": [2, 1] * 10, "b_right": range(20)}, npartitions=2)

result = dd.merge(left, right, broadcast=True)
assert hlg_layer(result.dask, "bcast-join")  # FAILS

result = dd.merge(left, right, broadcast=True, shuffle="tasks")
assert hlg_layer(result.dask, "bcast-join")  # PASSES
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

cc [user]

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
