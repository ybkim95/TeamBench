# GH1126_autogluon_4899: [timeseries] Allow using custom distr_output with the TFT model — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/autogluon/autogluon

## PR Description

*Issue #, if available:*

*Description of changes:*
- Make it possible to pass custom `distr_output` to the TFT model. Currently, passing the custom value leads to an exception because specifying both `quantiles` and `distr_output` triggers an assertion during initialization of the TFT model.
- Remove stale TODOs for GluonTS models


By submitting this pull request, I confirm that you can use, modify, copy, and redistribute this contribution, under the terms of your choice.

## PR Review Comments

**[user]** on `timeseries/src/autogluon/timeseries/models/gluonts/torch/models.py`:

Is the default for DeepAR really `QuantileOutput`?

**[user]** on `timeseries/src/autogluon/timeseries/models/gluonts/torch/models.py`:

Same as my comment for DeepAR.

**[user]** on `timeseries/tests/unittests/models/test_gluonts.py`:

What's the intended outcome when both `quantile_levels` and `distr_output` are specified? Are the `quantile_levels` still used in some way or completely ignored.

**[user]** on `timeseries/src/autogluon/timeseries/models/gluonts/torch/models.py`:

Oops, thanks for catching that! Accidentally modified the default value when copy-pasting. Fixed now

**[user]** on `timeseries/tests/unittests/models/test_gluonts.py`:

`quantile_levels` is the property of AutoGluon's `AbstractTimeSeriesModel`. It determines which columns are present in the returned forecast DataFrame (in addition to the `mean`). 

`distr_output` is a hyperparameter of the underlying GluonTS model. For TFT, there are two ways to create the GluonTS estimator/model:
1. Pass `quantiles: list[float]` (default) - this will set `distr_output` to `QuantileOutput(quantiles=quantiles)`
2. Pass `distr_output: gluonts.torch.distributions.Output`.

If both parameters are passed at the same time, the estimator raises an exception.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
