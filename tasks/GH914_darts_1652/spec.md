# GH914_darts_1652: fix/historical_forecasting_tft_futcov — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/unit8co/darts/issues/1547
- Repo: https://github.com/unit8co/darts

## Issue Description

**Describe the bug**
The `historical_forecasts()` for `TFTModel` and `NlinearModel` is missing one prediction.

**To Reproduce**
```python
from darts import TimeSeries
from darts.models import TFTModel,RNNModel
from darts.datasets import AirPassengersDataset
from darts.utils.timeseries_generation import datetime_attribute_timeseries
from darts.utils.likelihood_models import QuantileRegression
import numpy as np


series = AirPassengersDataset().load()
train = series[:100]
test = series[100:]

covariates = datetime_attribute_timeseries(series, attribute="year", one_hot=False)
covariates = covariates.stack(
    datetime_attribute_timeseries(series, attribute="month", one_hot=False)
)
covariates = covariates.stack(
    TimeSeries.from_times_and_values(
        times=series.time_index,
        values=np.arange(len(series)),
        columns=["linear_increase"],
    )
)
covariates = covariates.astype(np.float32)

covariates_train = covariates[:100]

input_chunk_length = 24
forecast_horizon = 12
tftmodel = TFTModel(
    input_chunk_length=input_chunk_length,
    output_chunk_length=forecast_horizon,
    hidden_size=64,
    lstm_layers=1,
    num_attention_heads=4,
    dropout=0.1,
    batch_size=16,
    n_epochs=300,
    add_relative_index=False,
    add_encoders=None,
    likelihood=QuantileRegression(
    ), 
    random_state=42,
)

tftmodel.fit(train, future_covariates=covariates_train, verbose=False,epochs=1)

print(f'test time series index {test.time_index}')
forecast_instances = tftmodel.historical_forecasts(series,future_covariates=covariates,start = test.time_index[0],forecast_horizon = forecast_horizon, retrain = False,verbose=False,
                last_points_only=False,
                overlap_end=False )
print(len(forecast_instances))
print(forecast_instances[0].time_index)
print(forecast_instances[-1].time_index)
```
```
test time series index DatetimeIndex(['1957-05-01', '1957-06-01', '1957-07-01', '1957-08-01',
               '1957-09-01', '1957-10-01', '1957-11-01', '1957-12-01',
               '1958-01-01', '1958-02-01', '1958-03-01', '1958-04-01',
               '1958-05-01', '1958-06-01', '1958-07-01', '1958-08-01',
               '1958-09-01', '1958-10-01', '1958-11-01', '1958-12-01',
               '1959-01-01', '1959-02-01', '1959-03-01', '1959-04-01',
               '1959-05-01', '1959-06-01', '1959-07-01', '1959-08-01',
               '1959-09-01', '1959-10-01', '1959-11-01', '1959-12-01',
               '1960-01-01', '1960-02-01', '1960-03-01', '1960-04-01',
               '1960-05-01', '1960-06-01', '1960-07-01', '1960-08-01',
               '1960-09-01', '1960-10-01', '1960-11-01', '1960-12-01'],
              dtype='datetime64[ns]', name='Month', freq='MS')
32
DatetimeIndex(['1957-05-01', '1957-06-01', '1957-07-01', '1957-08-01',
               '1957-09-01', '1957-10-01', '1957-11-01', '1957-12-01',
               '1958-01-01', '1958-02-01', '1958-03-01', '1958-04-01'],
              dtype='datetime64[ns]', name='Month', freq='MS')
DatetimeIndex(['1959-12-01', '1960-01-01', '1960-02-01', '1960-03-01',
               '1960-04-01', '1960-05-01', '1960-06-01', '1960-07-01',
               '1960-08-01', '1960-09-01', '1960-10-01', '1960-11-01'],
              dtype='datetime64[ns]', name='Month', freq='MS')
```
**Expected behavior**

I am expecting the list of timeseries produced by `historical_forecasts()` to start with the `start`, which is expected. The last time series should end the same as the input `series`. In this case, it should be `1960-12-01` instead of `1960-11-01`. Meanwhile, the `RNNModel` is giving me the expected output. 

**System (please complete the following information):**
 - Python version: 3.9.15
 - darts version 0.23.1

**Additional context**
RNN model produces one more forecast instance. 
```python
rnnmodel = RNNModel(
    input_chunk_length=input_chunk_length,
    output_chunk_length=forecast_horizon,
    add_encoders=None,
    likelihood=QuantileRegression(
    ), 
    random_state=42,
)
rnnmodel.fit(train, future_covariates=covariates_train, verbose=False,epochs=1)

rnn_forecast_instances = rnnmodel.historical_forecasts(series,future_covariates=covariates,start = test.time_index[0],forecast_horizon = forecast_horizon, retrain = False,verbose=False,
                last_points_only=False,
                overlap_end=False )
print(len(rnn_forecast_instances))
print(rnn_forecast_instances[0].time_index)
print(rnn_forecast_instances[-1].time_index)
```
```
33
DatetimeIndex(['1957-05-01', '1957-06-01', '1957-07-01', '1957-08-01',
               '1957-09-01', '1957-10-01', '1957-11-01', '1957-12-01',
               '1958-01-01', '1958-02-01', '1958-03-01', '1958-04-01'],
              dtype='datetime64[ns]', name='Month', freq='MS')
DatetimeIndex(['1960-01-01', '1960-02-01', '1960-03-01', '1960-04-01',
               '1960-05-01', '1960-06-01', '1960-07-01', '1960-08-01',
               '1960-09-01', '1960-10-01', '1960-11-01', '1960-12-01'],
              dtype='datetime64[ns]', name='Month', freq='MS')
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hey [user], that seems strange indeed. Thanks for reporting! Let us do some investigation

### Comment 2 ([user]):

I tested this and indeed there is a bug in historical forecasts when getting the forecastable indexes with future covariates.
I tried only using encoders to generate the future covariates and that works (i.e. not passing `future_covariates` to `historical_forecasts()`).

[user] could you maybe have a look at this?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
