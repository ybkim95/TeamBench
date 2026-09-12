# GH1124_featuretools_2434: Fix scalar comparison primitives that can fail during feature calculation in some cases — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/alteryx/featuretools/issues/2080
- Repo: https://github.com/alteryx/featuretools

## Issue Description

There are four binary comparison primitives that can generate features that fail on feature calculation in some cases. The failures primarily appear to be in situations where a `Datetime` input is being compared to a scalar value.

The four primitives that have been found to cause this error are:
- `greater_than_equal_to_scalar`
- `greater_than_scalar`
- `less_than_scalar`
- `less_than_equal_to_scalar`

#### Code Sample, a copy-pastable example to reproduce your bug.

```python
import pandas as pd
import featuretools as ft

df = pd.DataFrame({
    "id": [0, 1, 2],
    "dates": pd.to_datetime(["2020-01-01", "2020-02-01" ,"2020-03-01"]),
    "ints": [100, 200, 300]
})

es = ft.EntitySet()
es.add_dataframe(dataframe_name="df", dataframe=df, index="id")

fm, features = ft.dfs(entityset=es, target_dataframe_name="df", trans_primitives=["greater_than_scalar"], max_depth=1)
```

```
TypeError: Invalid comparison between dtype=datetime64[ns] and int
```

These primitives should be updated to either allow the calculation to proceed without error. Alternatively, the `Datetime` input could be removed from the list of supported inputs, or the input types list could perhaps be dynamically updated on instantiation based on the type of the scalar value provided.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

We may also want to consider updating the `EqualScalar` primitive even though it does not seem to produce the same error. Seems like maybe we should only use numeric inputs for all of these primitives.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
