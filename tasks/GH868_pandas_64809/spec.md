# GH868_pandas_64809: BUG: fix dt64[non_nano] + offsets with sub-unit offset parameter — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pandas-dev/pandas/issues/56586
- Repo: https://github.com/pandas-dev/pandas

## Issue Description

```python
import pandas as pd

dti  = pd.date_range("2016-01-01", periods=3, unit="s")

dti + pd.offsets.CustomBusinessDay(offset=pd.Timedelta(1))
dti + pd.offsets.BusinessHour(offset=pd.Timedelta(1))
dti + pd.offsets.CustomBusinessHour(offset=pd.Timedelta(1))
dti + pd.offsets.CustomBusinessMonthBegin(offset=pd.Timedelta(1))
dti + pd.offsets.CustomBusinessMonthEnd(offset=pd.Timedelta(1))
```

Each of the additions above incorrectly round the result when calling `as_unit(self.unit)` [here](https://github.com/pandas-dev/pandas/blob/main/pandas/core/arrays/datetimes.py#L819).

The best solution would be to implement _apply_array for all of these offsets and make the pointwise path in _add_offset unnecessary.

Next best would be something like

```
res_unit = self.unit
if hasattr(offset, "offset"):
    unit = Timedelta(offset.offset).unit
    res_unit = max(self.unit, unit)  # <- not actually "max"; we probably have a helper for this
dtype = tz_to_dtype(self.tz, unit=res_unit)
result = type(self)._from_sequence(res_values, dtype=dtype)
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
