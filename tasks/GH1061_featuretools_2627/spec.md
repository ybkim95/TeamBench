# GH1061_featuretools_2627: Fix bug in PercentTrue primitive — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/alteryx/featuretools/issues/2625
- Repo: https://github.com/alteryx/featuretools

## Issue Description

PercentTrue calculation can fail on BooleanNullable inputs when there are no values to aggregate

#### Code Sample, a copy-pastable example to reproduce your bug.

```python
import featuretools as ft
import pandas as pd
from woodwork.logical_types import BooleanNullable

es = ft.EntitySet(id="customer_data")

customers_df = pd.DataFrame(data={"customer_id": [1, 2]})

es = es.add_dataframe(
    dataframe_name="customers_df",
    dataframe=customers_df,
    index="customer_id",
)

transactions_df = pd.DataFrame(data={"tx_id": [1], "customer_id": [1], "is_foo": [True]})

es = es.add_dataframe(
    dataframe_name="transactions_df",
    dataframe=transactions_df,
    index="tx_id",
    logical_types={"is_foo": BooleanNullable}
)

es = es.add_relationship("customers_df", "customer_id", "transactions_df", "customer_id")

feature_matrix, features_definitions = ft.dfs(
    entityset=es,
    target_dataframe_name="customers_df",
    agg_primitives=["percent_true"],
)

```

A potential solution to this is to change the primitive default value from 0 to `pd.NA`

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
