# GH951_darts_1465: fix historical forecasts retraining of TFMs — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/unit8co/darts/issues/1461
- Repo: https://github.com/unit8co/darts

## Issue Description

**Is your feature request related to a current problem? Please describe.**
`historical_forecasts()` retrains the same model instance on the new training section instead of using a brand-new model instance.

**Additional context**
The example code below shows that `historical_forecasts()` gives the same results as calling the `fit()` method multiple times on the same model instance. However, I would expect the outputs of `historical_forecasts()` to be the same as fitting a brand-new model instance, with the same parameters, on each training section.
```
from darts.datasets import AirPassengersDataset
from darts.dataprocessing.transformers import Scaler
from darts.models.forecasting.block_rnn_model import BlockRNNModel
import pandas as pd

# A function for instantiating a rnn model with the initial weights fixed
def instantiate_BlockRNNModel():
    return BlockRNNModel(
        input_chunk_length=12,
        output_chunk_length=6,
        model='RNN',
        hidden_dim=10,
        n_rnn_layers=1,
        hidden_fc_sizes=None,
        dropout=0,
        n_epochs=5,
        batch_size=16,
        optimizer_kwargs={"lr": 1e-3},
        random_state=42,
        save_checkpoints=True
    )

# Prepare the data
series = AirPassengersDataset().load()
transformer = Scaler()
series_transformed = transformer.fit_transform(series)

# 1. `historical_forecasts()`, it is a 3-pass historical_forecast
model = instantiate_BlockRNNModel()
historical_forecasts_result = model.historical_forecasts(
    series_transformed,
    start=len(series_transformed)-3*6,
    train_length=None,
    forecast_horizon=6,
    stride=6,
    retrain=True,
    verbose=False,
    last_points_only=False
)
historical_forecasts_result = [forecast.values() for forecast in historical_forecasts_result]

# 2. As far as I know, `historical_forecasts()` is similar to calling `fit()` on the same model with 3 training sections
train_set_1, val_set_1 = series_transformed.split_after(pd.Timestamp('19590601'))
train_set_2, val_set_2 = series_transformed.split_after(pd.Timestamp('19591201'))
train_set_3, val_set_3 = series_transformed.split_after(pd.Timestamp('19600601'))

individual_forecasts_by_same_model = []
same_model = instantiate_BlockRNNModel()
same_model.fit(train_set_1, verbose=True)
individual_forecasts_by_same_model.append(same_model.predict(n=6).values())
same_model.fit(train_set_2, verbose=True)
individual_forecasts_by_same_model.append(same_model.predict(n=6).values())
same_model.fit(train_set_3, verbose=True)
individual_forecasts_by_same_model.append(same_model.predict(n=6).values())

# 3. Fitting three individual model instances with 3 training sections
# From the previous two parts, `historical_forecasts_result` is the same as `individual_forecasts_by_same_model`
# However, I would expect the results given by the `historical_forecasts()` to be the same as 
# fitting a brand-new model on each training section, like the following `individual_forecasts_by_different_models`.
train_set_1, val_set_1 = series_transformed.split_after(pd.Timestamp('19590601'))
train_set_2, val_set_2 = series_transformed.split_after(pd.Timestamp('19591201'))
train_set_3, val_set_3 = series_transformed.split_after(pd.Timestamp('19600601'))

individual_model_1 = instantiate_BlockRNNModel()
individual_model_2 = instantiate_BlockRNNModel()
individual_model_3 = instantiate_BlockRNNModel()
individual_model_1.fit(train_set_1, verbose=True)
individual_model_2.fit(train_set_2, verbose=True)
individual_model_3.fit(train_set_3, verbose=True)
individual_forecasts_by_different_models = [
    model.predict(n=6).values() 
    for model
    in [individual_model_1, individual_model_2, individual_model_3]
]
```

Result
```
historical_forecasts_result:
[array([[0.40726016],
        [0.14743934],
        [0.42281431],
        [0.30751979],
        [0.3935865 ],
        [0.23179494]]),
 array([[0.40049573],
        [0.38148109],
        [0.45629141],
        [0.3826234 ],
        [0.38148096],
        [0.40922707]]),
 array([[0.53207854],
        [0.50775845],
        [0.5872545 ],
        [0.43763365],
        [0.43169829],
        [0.55752873]])]

individual_forecasts_by_same_model:
[array([[0.40726016],
        [0.14743934],
        [0.42281431],
        [0.30751979],
        [0.3935865 ],
        [0.23179494]]),
 array([[0.40049573],
        [0.38148109],
        [0.45629141],
        [0.3826234 ],
        [0.38148096],
        [0.40922707]]),
 array([[0.53207854],
        [0.50775845],
        [0.5872545 ],
        [0.43763365],
        [0.43169829],
        [0.55752873]])]

individual_forecasts_by_different_models
[array([[0.40726016],
        [0.14743934],
        [0.42281431],
        [0.30751979],
        [0.3935865 ],
        [0.23179494]]),
 array([[0.402741  ],
        [0.15947664],
        [0.42768211],
        [0.34189958],
        [0.42966399],
        [0.25139858]]),
 array([[0.46655868],
        [0.2012079 ],
        [0.50961595],
        [0.35336985],
        [0.44060068],
        [0.28922872]])]
```

**Describe proposed solution**
Save the model before any training, and load the untrained model before retraining.
Alternatively, reset the model to its initial weights before retraining.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi [user], and thanks for raising this issue.

It is true that currently `historical_forecasts` trains the same model object multiple times. I agree that this is an issue for our deep learning models as instead of retraining a fresh model, we are more "fine-tuning" the existing model.

We can easily create a fresh model object with `model_new = model.untrained_model()`.

I opened a PR to address this: #1465

### Comment 2 ([user]):

Thanks for raising! I think this may have been introduced in 0.23.0 with the new multi-series backtesting feature. We should include the fix in 0.23.1.

## PR Review Comments

**[user]** on `darts/models/forecasting/forecasting_model.py`:

I'm thinking we should always call `untrained_model()` even for the first pass here, WDYT?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
