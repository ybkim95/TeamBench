# GH1062_autogluon_5436: [timeseries] fix predict_time computation in ensembles — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/autogluon/autogluon

## PR Description

*Issue #, if available:*

*Description of changes:*


By submitting this pull request, I confirm that you can use, modify, copy, and redistribute this contribution, under the terms of your choice.

## PR Review Comments

**[user]** on `timeseries/src/autogluon/timeseries/trainer/ensemble_composer.py`:

After the assertion above, can we keep this as `predict_time = model.predict_time_marginal`?

**[user]** on `timeseries/src/autogluon/timeseries/models/abstract/abstract_timeseries_model.py`:

We never use this for time series models, should we just avoid setting this attribute?

**[user]** on `timeseries/src/autogluon/timeseries/models/abstract/abstract_timeseries_model.py`:

iirc, HPO machinery depends nontrivially on this and therefore I could not remove it.

**[user]** on `timeseries/src/autogluon/timeseries/trainer/ensemble_composer.py`:

thanks!

**[user]** on `timeseries/src/autogluon/timeseries/models/abstract/abstract_timeseries_model.py`:

All right, let's keep it then

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
