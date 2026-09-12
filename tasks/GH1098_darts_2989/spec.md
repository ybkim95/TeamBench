# GH1098_darts_2989: Fix: StaticCovariatesTransformer cols_cat order differing from column order — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/unit8co/darts/issues/2988
- Repo: https://github.com/unit8co/darts

## Issue Description

**Describe the bug**

The `StaticCovariatesTransformer` creates incorrect one-hot encoded column names when the order specified in the `cols_cat` parameter differs from the actual column order in the data. This results in column names that combine the wrong feature names with the wrong category values (e.g., `City_US` and `Country_New York` instead of `City_New York` and `Country_US`).

**To Reproduce**

```python
import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from darts import TimeSeries
from darts.dataprocessing.transformers import StaticCovariatesTransformer

# 1. Create data with columns in order: [Country, City]
df = pd.DataFrame({"Country": ["US", "China"], "City": ["New York", "Beijing"]})
series = [TimeSeries.from_values(np.ones((5, 1)), static_covariates=df.iloc[[i]]) for i in range(2)]

# 2. Initialize transformer with different order: [City, Country]
transformer = StaticCovariatesTransformer(
    transformer_cat=OneHotEncoder(sparse_output=False),
    cols_cat=["City", "Country"]  # This order differs from df.columns
)

# 3. Fit and Transform
transformed = transformer.fit_transform(series)

print("Actual Data Values: Country=US, City=New York")
print(f"Resulting Columns:  {transformed[0].static_covariates.columns.tolist()}")
print("\nTransformed Values:")
print(transformed[0].static_covariates.to_string())
```

**Expected behavior**

For the first series with `Country="US"` and `City="New York"`, the expected one-hot encoded columns should be:
- `City_New York = 1.0`
- `City_Beijing = 0.0`
- `Country_US = 1.0`
- `Country_China = 0.0`

**Actual behavior**

```
Actual Data Values: Country=US, City=New York
Resulting Columns:  ['Country_Beijing', 'Country_New York', 'City_China', 'City_US']

Transformed Values:
static_covariates  Country_Beijing  Country_New York  City_China  City_US
0                              0.0               1.0         0.0      1.0
```

The column names are **incorrect**:
- `Country_New York = 1.0` (should be `City_New York`)
- `City_US = 1.0` (should be `Country_US`)

The "Country" feature has city names, and the "City" feature has country names.

**System**
 - Python version: 3.13.7
 - darts version: 0.40.0

## PR Review Comments

**[user]** on `darts/dataprocessing/transformers/static_covariates_transformer.py`:

Looks great [user]! I agree with [user] that it would be more robust for the future if we performed the same operation for both `cols_num` and `cols_cat`. I would suggest to combine `_infer_static_cov_dtypes()` and `_create_component_masks()` into one method (and remove the old ones) that returns both processed column names and masks.

e.g. something like below:

```
    @staticmethod
    def _process_static_cov_columns(
        stat_covs: pd.DataFrame,
        cols_num: Optional[Sequence[str]],
        cols_cat: Optional[Sequence[str]],
    ) -> tuple[list[str], list[str], np.ndarray, np.ndarray]:
        """
        Extracts numerical and categorical static covariate (component / columns) names and their component masks 
        in order of the input data.
        """
        if cols_num is None:
            mask_num = stat_covs.columns.isin(
                stat_covs.select_dtypes(include=np.number).columns
            )
        else:
            mask_num = stat_covs.columns.isin(cols_num)
        cols_num = stat_covs.columns[mask_num].tolist()

        if cols_cat is None:
            mask_cat = stat_covs.columns.isin(
                stat_covs.select_dtypes(exclude=np.number).columns
            )
        else:
            mask_cat = stat_covs.columns.isin(cols_cat)
        cols_cat = stat_covs.columns[mask_cat].tolist()
        return cols_num, cols_cat, mask_num, mask_cat
```

That would simplify things a bit and we can also revert all changes below

**[user]** on `darts/tests/dataprocessing/transformers/test_static_covariates_transformer.py`:

Instead of comparing two sets of columns, we should rather check that both series have the expected column order (e.g. compare lists)

**[user]** on `darts/tests/dataprocessing/transformers/test_static_covariates_transformer.py`:

These could also be simplified to (might be easier to compare the two series)

```suggestion
    assert first_static_covs.iloc[0].tolist() == [1.0, 0.0, 1.0, 0.0]
```

**[user]** on `darts/dataprocessing/transformers/static_covariates_transformer.py`:

I agree, thanks for the suggestion! 👍

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
