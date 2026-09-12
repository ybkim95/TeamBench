# GH1103_darts_2869: Fix/hfc retrain with tfm and ocs — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/unit8co/darts/issues/2848
- Repo: https://github.com/unit8co/darts

## Issue Description

**Describe the bug**

historical_forecasts fails with output_chunk_shift >0

**To Reproduce**

```python
from darts.datasets import WeatherDataset
from darts.models import DLinearModel
series = WeatherDataset().load()
target = series['p (mbar)'][:100]
model = DLinearModel(
    input_chunk_length=6,
    output_chunk_length=6,
    output_chunk_shift=1, # <- error only with shift
    n_epochs=1,
)
preds = model.historical_forecasts(
    target,
    last_points_only=False,
    retrain=10_000, # (Only train once)
    verbose=False,
    overlap_end=False,
)
```

```sh
ValueError: The train dataset does not contain even one training sample. This is likely due to the provided training series being too short. This model expect series of length at least 13.
```


**System (please complete the following information):**
 - Python version: 3.11.13
 - darts version: 0.36.0

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

It's probably due to wrong START calculation, because it works when you calculate it manually:

```python
preds = model.historical_forecasts(
    target,
    last_points_only=False,
    retrain=10_000, # (Only train once)
    # FIXED with input_chunk_length + output_chunk_length + output_chunk_shift
    start=series[6+6+1].start_time(), 
    verbose=False,
    overlap_end=False,
)
```

### Comment 2 ([user]):

Hi [user] and thanks for raising this issue. It indeed seems to be a bug. I tested and it only happens for `TorchForecastingModel` (test with `RegressionModel` worked as expected).

I'll add it to our backlog.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
