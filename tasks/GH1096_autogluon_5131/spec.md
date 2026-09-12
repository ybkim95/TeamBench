# GH1096_autogluon_5131: [timeseries] Avoid masking the 'scaler' param with the default 'target_scaler' value — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/autogluon/autogluon

## PR Description

*Issue #, if available:*

*Description of changes:*
- Prior to v1.3.0, users could set the `scaler` hyperparameter to choose the scaling option in MLForecast models. In v1.3.0, we renamed this hyperparameter to `target_scaler` for consistency with other models. We intended to support the `scaler` hyperparameter as well for backwards compatibility. However, because of a bug in the logic, `scaler` was always shadowed by the default value of the `target_scaler`, so the old parameter name got effectively deprecated. This can result in unexpected performance changes to the users. This PR fixes this problem.


By submitting this pull request, I confirm that you can use, modify, copy, and redistribute this contribution, under the terms of your choice.

## PR Review Comments

**[user]** on `timeseries/src/autogluon/timeseries/models/autogluon_tabular/mlforecast.py`:

We could, in theory, add a `FutureWarning` here and deprecate the old name in v2.0. However, this looks like such a minor overhead to maintain that I'm leaning towards just keeping this around forever.

**[user]** on `timeseries/src/autogluon/timeseries/models/autogluon_tabular/mlforecast.py`:

What happens if user provides both `scaler` and `target_scaler`? Should we raise or warn?

**[user]** on `timeseries/src/autogluon/timeseries/models/autogluon_tabular/mlforecast.py`:

It should be okay to keep this around imo.

**[user]** on `timeseries/src/autogluon/timeseries/models/autogluon_tabular/mlforecast.py`:

Also, does this imply any documentation changes?

**[user]** on `timeseries/src/autogluon/timeseries/models/autogluon_tabular/mlforecast.py`:

Before this PR: `scaler` is always ignored, only `target_scaler` matters.
This PR (at the time of review): `scaler` takes precedence over `target_scaler` (probably not ideal)

I have updated the PR so that `target_scaler` takes precedence over `scaler` - that seems more reasonable to me.

We don't need to update the docs - they already only reference the new name `target_scaler`.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
