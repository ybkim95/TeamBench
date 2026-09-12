# GH1102_darts_2895: fix: properly save naive model — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/unit8co/darts/issues/2839
- Repo: https://github.com/unit8co/darts

## Issue Description

**Describe the bug**

Trying to save a global baseline model (GlobalNaiveSeasonal, GlobalNaiveAggregate, GlobalNaiveDrift) throws the following error.

> AttributeError: Saving a checkpoint is only possible if a model is attached to the Trainer. Did you call Trainer.save_checkpoint() before calling Trainer.{fit,validate,test,predict}?

**To Reproduce**

```python
from darts.models import LinearRegressionModel, RNNModel, GlobalNaiveSeasonal, GlobalNaiveAggregate, GlobalNaiveDrift
from darts.models.forecasting.forecasting_model import GlobalForecastingModel
from darts.models.forecasting.torch_forecasting_model import TorchForecastingModel
from darts.datasets import AirPassengersDataset

passengers = AirPassengersDataset().load()

# model = LinearRegressionModel(lags=1, output_chunk_length=1)  # works, global but not torch
# model = RNNModel(input_chunk_length=1, n_epochs=10)  # works, torch
# model = GlobalNaiveSeasonal(input_chunk_length=input_steps, output_chunk_length=1)  # doesn't work, torch without weights
# model = GlobalNaiveAggregate(input_chunk_length=1, output_chunk_length=1)  # doesn't work, torch without weights
model = GlobalNaiveDrift(input_chunk_length=1, output_chunk_length=1)  # doesn't work, torch without weights

model.fit(passengers)

path = "model"
model.save(path)  # <---- fails here

# make sure loading works too.
# Unfortunately, you cannot use GlobalForecastingModel.load for torch models :(
# model = GlobalForecastingModel.load(path)
model = TorchForecastingModel.load(path)
```

**Expected behavior**

The model is saved with all required information so that it can be loaded with TorchForecastingModel.load (or even better GlobalForecastingModel.load).

**System (please complete the following information):**

- Python version: 3.12.9
- darts version: 0.35.0

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi [user] and thanks for raising this issue. Indeed saving and loading is not supported since we never actually train the global baselines when calling `fit()` (therefore the module is not attached to the trainer, and no checkpoint can be created). 

So technically, you can just fit the model before inference without any performance loss. I do agree however that we should support proper saving / loading to have the same user flow also for global baseline models. I'll add it to our backlog!

## PR Review Comments

**[user]** on `CHANGELOG.md`:

we always point at the PR directly instead of the issue :) 

```suggestion
- Fixed a bug when saving a `GlobalNaiveModel` directly after fitting it (without performing prediction). [#2895]((withheld: the upstream fix is not part of the task)), by [Alain Gysi](https://github.com/Kurokabe)
```

**[user]** on `darts/tests/models/forecasting/test_global_forecasting_models.py`:

Testing only `GlobalNaiveSeasonal` is fine since they all use the same base model logic behind the hood

```suggestion
```

**[user]** on `darts/tests/models/forecasting/test_global_forecasting_models.py`:

I would suggest that instead of adding a complete new test here, you could just extend `test_save_load_model()` to store an additional model save right after `fit()`, and then load it and compare it to the other predictions. It's good to test this for all the other models as well :)

**[user]** on `darts/models/forecasting/global_baseline_models.py`:

Nice, this is definitely a solution that would work :) 

There is a downside to this though that we would have to run the prediction on all time series (it can be thousands of series).

To avoid this, I would suggest we try out something `trainer.strategy.connect(model)` to connect the model to the trainer's strategy.

You could put it in the `else:` condition [here](https://github.com/unit8co/darts/blob/8821f5109a59605f25a0a259c3f36ac31d094ac8/darts/models/forecasting/torch_forecasting_model.py#L1316).

What do you think?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
