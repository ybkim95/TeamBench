# GH1171_FLAML_1469: Fix log_training_metric causing IndexError for time series models — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/microsoft/FLAML/issues/1464
- Repo: https://github.com/microsoft/FLAML

## Issue Description

### Describe the bug

The key findings are:

Individual TS estimators (arima, sarimax, holt-winters) FAIL with log_training_metric=True
ML estimators (xgboost, lgbm, catboost) PASS
When log_training_metric is NOT set, arima PASSES (see the holdout split test)


ROOT CAUSE HYPOTHESIS:
- `log_training_metric=True` causes FLAML to call get_y_pred() on X_train
- For time series models (arima, sarimax, holt-winters), this fails because
  the TS model's predict() method expects X to have timestamps, but during
  internal validation, X_train can be empty or malformed.




### Steps to reproduce

Script for reproduction
```
"""
FLAML Root Cause Verification Test

Hypothesis: The bug is triggered by `log_training_metric=True` with time series models.

When log_training_metric=True, FLAML tries to compute training predictions
via get_y_pred() which calls estimator.predict(X_train). For TS models,
this fails because X_train can be empty during certain validation scenarios.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import sktime.datasets
from flaml import AutoML

def prepare_airline_data():
    """Prepare Airline data in FLAML format."""
    airline = sktime.datasets.load_airline()
    airline.index = airline.index.to_timestamp()
    
    return pd.DataFrame({
        "ds": airline.index,
        "y": airline.values.astype(np.float64),
    })


def test_log_training_metric_hypothesis():
    """Test if log_training_metric=True is the root cause."""
    print("\n" + "="*70)
    print("ROOT CAUSE VERIFICATION: log_training_metric")
    print("="*70)
    
    train_df = prepare_airline_data()
    
    # Base config
    base_config = {
        "task": "ts_forecast",
        "time_budget": 10,
        "metric": "mape",
        "eval_method": "holdout",
        "seed": 42,
        "verbose": 0,
        "estimator_list": ["arima"],
    }
    
    # Test 1: WITHOUT log_training_metric
    print("\n--- Test 1: WITHOUT log_training_metric ---")
    config1 = base_config.copy()
    
    try:
        automl = AutoML()
        automl.fit(dataframe=train_df, label="y", period=1, **config1)
        print(f"  ✅ SUCCESS - Best: {automl.best_estimator}")
    except Exception as e:
        print(f"  ❌ FAILED - {type(e).__name__}: {e}")
    
    # Test 2: WITH log_training_metric=True
    print("\n--- Test 2: WITH log_training_metric=True ---")
    config2 = base_config.copy()
    config2["log_training_metric"] = True
    
    try:
        automl = AutoML()
        automl.fit(dataframe=train_df, label="y", period=1, **config2)
        print(f"  ✅ SUCCESS - Best: {automl.best_estimator}")
    except Exception as e:
        print(f"  ❌ FAILED - {type(e).__name__}: {e}")
    
    # Test 3: WITH log_training_metric=False (explicit)
    print("\n--- Test 3: WITH log_training_metric=False ---")
    config3 = base_config.copy()
    config3["log_training_metric"] = False
    
    try:
        automl = AutoML()
        automl.fit(dataframe=train_df, label="y", period=1, **config3)
        print(f"  ✅ SUCCESS - Best: {automl.best_estimator}")
    except Exception as e:
        print(f"  ❌ FAILED - {type(e).__name__}: {e}")


def test_all_ts_estimators_with_and_without_logging():
    """Test all TS estimators with and without log_training_metric."""
    print("\n" + "="*70)
    print("ALL TS ESTIMATORS: with/without log_training_metric")
    print("="*70)
    
    train_df = prepare_airline_data()
    
    ts_estimators = ["arima", "sarimax", "holt-winters"]
    
    for est in ts_estimators:
        print(f"\n--- Estimator: {est} ---")
        
        # Without logging
        config_no_log = {
            "task": "ts_forecast",
            "time_budget": 5,
            "metric": "mape",
            "eval_method": "holdout",
            "seed": 42,
            "verbose": 0,
            "estimator_list": [est],
        }
        
        try:
            automl = AutoML()
            automl.fit(dataframe=train_df, label="y", period=1, **config_no_log)
            print(f"  log_training_metric=False: ✅ SUCCESS")
        except Exception as e:
            print(f"  log_training_metric=False: ❌ FAILED - {str(e)[:50]}")
        
        # With logging
        config_with_log = config_no_log.copy()
        config_with_log["log_training_metric"] = True
        
        try:
            automl = AutoML()
            automl.fit(dataframe=train_df, label="y", period=1, **config_with_log)
            print(f"  log_training_metric=True:  ✅ SUCCESS")
        except Exception as e:
            print(f"  log_training_metric=True:  ❌ FAILED - {str(e)[:50]}")


def test_fix_remove_log_training_metric():
    """Test the fix: remove log_training_metric from config."""
    print("\n" + "="*70)
    print("FIX VERIFICATION: BALANCED config without log_training_metric")
    print("="*70)
    
    train_df = prepare_airline_data()
    
    # Original BALANCED config (fails)
    original_config = {
        "task": "ts_forecast",
        "time_budget": 30,
        "metric": "mape",
        "eval_method": "holdout",
        "seed": 42,
        "verbose": 0,
        "estimator_list": ["arima", "sarimax", "holt-winters"],
        "log_training_metric": True,  # <-- THE BUG
        "log_file_name": "flaml_balanced.log",
    }
    
    # Fixed config (should work)
    fixed_config = {
        "task": "ts_forecast",
        "time_budget": 30,
        "metric": "mape",
        "eval_method": "holdout",
        "seed": 42,
        "verbose": 0,
        "estimator_list": ["arima", "sarimax", "holt-winters"],
        # log_training_metric REMOVED
        "log_file_name": "flaml_balanced.log",
    }
    
    print("\n--- Original BALANCED config (with log_training_metric=True) ---")
    try:
        automl = AutoML()
        automl.fit(dataframe=train_df, label="y", period=1, **original_config)
        print(f"  ✅ SUCCESS - Best: {automl.best_estimator}")
    except Exception as e:
        print(f"  ❌ FAILED - {type(e).__name__}: {str(e)[:50]}")
    
    print("\n--- Fixed BALANCED config (without log_training_metric) ---")
    try:
        automl = AutoML()
        automl.fit(dataframe=train_df, label="y", period=1, **fixed_config)
        print(f"  ✅ SUCCESS - Best: {automl.best_estimator}")
    except Exception as e:
        print(f"  ❌ FAILED - {type(e).__name__}: {str(e)[:50]}")


def test_via_forecaster_with_fix():
    """Test the fix via FlamlTsForecaster."""
    print("\n" + "="*70)
    print("FIX VERIFICATION: Via FlamlTsForecaster")
    print("="*70)
    
    from src.estimater.forecasting.flaml_ts_forecaster import FlamlTsForecaster
    from sktime.forecasting.base import ForecastingHorizon
    
    airline = sktime.datasets.load_airline()
    
    # Fixed config
    fixed_config = {
        "task": "ts_forecast",
        "time_budget": 30,
        "metric": "mape",
        "eval_method": "holdout",
        "seed": 42,
        "verbose": 0,
        "estimator_list": ["arima", "sarimax", "holt-winters"],
        # log_training_metric REMOVED
    }
    
    forecaster = FlamlTsForecaster(
        flaml_ts_model=AutoML,
        model_init_params={},
        model_fit_params=fixed_config,
    )
    
    fh = ForecastingHorizon(np.arange(1, 2))
    
    print("\n--- Testing FlamlTsForecaster with fixed config ---")
    try:
        forecaster.fit(y=airline, fh=fh)
        print(f"  ✅ SUCCESS - Best model: {forecaster._forecaster_name}")
        
        # Also test prediction
        pred = forecaster.predict(fh=fh)
        print(f"  ✅ Prediction: {pred.values}")
        return True
    except Exception as e:
        print(f"  ❌ FAILED - {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "#"*70)
    print("# FLAML ROOT CAUSE VERIFICATION")
    print("#"*70)
    
    test_log_training_metric_hypothesis()
    test_all_ts_estimators_with_and_without_logging()
    test_fix_remove_log_training_metric()
    test_via_forecaster_with_fix()
    
    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    print("""

```

### Model Used

arima, sarimax, holt-winters

### Expected Behavior

All forecasters work with and without `log_training_metric=True` 

### Screenshots and logs

######################################################################
# FLAML ROOT CAUSE VERIFICATION
######################################################################

======================================================================
ROOT CAUSE VERIFICATION: log_training_metric
======================================================================

--- Test 1: WITHOUT log_training_metric ---
/home/mirko/git/metaforecast-thesis/venv/lib/python3.10/site-packages/statsmodels/tsa/base/tsa_model.py:471: ValueWarning: No frequency information was provided, so inferred frequency MS will be used.
  self._init_dates(dates, freq)
/home/mirko/git/metaforecast-thesis/venv/lib/python3.10/site-packages/statsmodels/tsa/base/tsa_model.py:471: ValueWarning: No frequency information was provided, so inferred frequency MS will be used.
  self._init_dates(dates, freq)
/home/mirko/git/metaforecast-thesis/venv/lib/python3.10/site-packages/statsmodels/tsa/base/tsa_model.py:471: ValueWarning: No frequency information was provided, so inferred frequency MS will be used.
  self._init_dates(dates, freq)
  ✅ SUCCESS - Best: arima

--- Test 2: WITH log_training_metric=True ---
  ❌ FAILED - IndexError: single positional indexer is out-of-bounds

--- Test 3: WITH log_training_metric=False ---
  ✅ SUCCESS - Best: arima

======================================================================
ALL TS ESTIMATORS: with/without log_training_metric
======================================================================

--- Estimator: arima ---
  log_training_metric=False: ✅ SUCCESS
  log_training_metric=True:  ❌ FAILED - single positional indexer is out-of-bounds

--- Estimator: sarimax ---
  log_training_metric=False: ✅ SUCCESS
  log_training_metric=True:  ❌ FAILED - single positional indexer is out-of-bounds

--- Estimator: holt-winters ---
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
  log_training_metric=False: ✅ SUCCESS
Regressors are ignored for Holt-Winters ETS models.
  log_training_metric=True:  ❌ FAILED - single positional indexer is out-of-bounds

======================================================================
FIX VERIFICATION: BALANCED config without log_training_metric
======================================================================

--- Original BALANCED config (with log_training_metric=True) ---
  ❌ FAILED - IndexError: single positional indexer is out-of-bounds

--- Fixed BALANCED config (without log_training_metric) ---
  ✅ SUCCESS - Best: arima

======================================================================
FIX VERIFICATION: Via FlamlTsForecaster
======================================================================

--- Testing FlamlTsForecaster with fixed config ---
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
Regressors are ignored for Holt-Winters ETS models.
  ✅ SUCCESS - Best model: holt-winters
  ✅ Prediction: [444.20952783]



### Additional Information

FLAML Version:  flaml[forecasting]==2.3.6
Operating System: 
Distributor ID: Ubuntu
Description:    Ubuntu 22.04.1 LTS
Release:        22.04
Codename:       jammy
Python Version: Python 3.10.12
Related Issues: -

## PR Review Comments

**[user]** on `flaml/automl/ml.py`:

The comment could be more specific about why training metrics can't be computed for TimeSeriesDataset. Consider clarifying that attempting to call predict() on TimeSeriesDataset with training data would fail because the time series model's predict method requires properly configured test_data within the dataset, which X_train doesn't have in the expected format for prediction.
```suggestion
            # For time series tasks, skip computing training metrics: calling predict() on a
            # TimeSeriesDataset built from training data would fail because the time series model's
            # predict() expects properly configured test_data inside the dataset, which X_train lacks.
```

**[user]** on `test/automl/test_forecast.py`:

The try-except block that catches all exceptions and re-raises them doesn't add value in a pytest test. Pytest will automatically catch and report any exceptions. Consider removing lines 710-716 and directly calling automl.fit() followed by the assertions, or only catch specific expected exceptions if you want to provide custom error messages.
```suggestion
        automl.fit(dataframe=df, **settings, period=time_horizon)
        print(f"  ✅ {estimator} SUCCESS with log_training_metric=True")
        assert automl.best_estimator == estimator
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
