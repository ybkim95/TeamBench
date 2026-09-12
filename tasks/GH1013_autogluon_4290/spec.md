# GH1013_autogluon_4290: [tabular] Fix Stacker max_models logic — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/autogluon/autogluon

## PR Description

*Issue #, if available:*

*Description of changes:*

- Fix a long standing major bug where L2+ stacker models that are not weighted ensembles will not respect the `max_models` and `max_models_per_type` parameters, and will instead use all base models during fit.
- This bug has been present forever, since the original code was written, but only started majorly impacting AutoGluon in v1.0+ with the introduction of Zeroshot-HPO.
- Fixing this should lead to faster training and inference times for stack layers, and a potential quality improvement.

Results: 3x inference speedup with no noticeable model quality drop:

![pr4290_boxplot](https://github.com/autogluon/autogluon/assets/16392542/783da815-87d5-40df-897e-f7d9b8e91532)

TODO:

- [x] Benchmark `best` and `high` quality presets.
- [x] Consider changing defaults for `max_models` and `max_models_per_type`. Currently they are 25 and 5 respectively. Likely `max_models` should be increased to ~50.
- [x] Add additional documentation for `get_feature_metadata` in Trainer.
- [x] Add advanced unit tests.

Follow-up PRs:

- [ ] Potentially delete StackerEnsembleModel, move logic to Trainer.
- [ ] Add option for user to specify WeightedEnsemble max_models and max_models_per_type
- [ ] Remove `base_models_dict` parameter.
- [x] Bug: `sample_weight` column is present in `X` in the `model.fit` call, it should not be present. (Created issue: https://github.com/autogluon/autogluon/issues/4304)
- [x] Bug: `sample_weight` column is passed to `feature_prune` if both sample_weight and feature_prune are enabled. This shouldn't happen. (Created issue: https://github.com/autogluon/autogluon/issues/4304)

By submitting this pull request, I confirm that you can use, modify, copy, and redistribute this contribution, under the terms of your choice.

## PR Review Comments

**[user]** on `core/src/autogluon/core/models/ensemble/stacker_ensemble_model.py`:

How did we arrive at 12?
Also, what is the reason behind changing `max_models_per_type` based on the no. of rows in the data?

**[user]** on `core/src/autogluon/core/models/abstract/abstract_model.py`:

qq: why did we move it here?

**[user]** on `core/src/autogluon/core/models/ensemble/stacker_ensemble_model.py`:

12 is an arbitrary stopping point, but the intuition is that 12 should be close to approximating uncapped, and will behave much much better than if it is left uncapped if a user uses HPO and fits 1000s of models as an example.

This logic is not optimal, but it is better than a fixed value. We can iterate on the exact thresholds and values in future PRs.

The reason for changing the value depending on num_rows is that doing this shows improvement over a fixed value on TabRepo simulations. The intuition is that larger `max_models_per_type` leads to more overfitting, and you can counter overfitting by having more data.

**[user]** on `core/src/autogluon/core/models/abstract/abstract_model.py`:

Good question!

- In `self._preprocess_set_features` I added logic in this PR which updates `self.features to reflect which base_models are being used. Previously `self.features` wasn't correct and contained unused base models.
- In order to know which `base_models` are being used, I need to run the logic which filters base_models based on `max_models` and `max_models_per_type`.
- In order to run the filtering logic, I first need to know the hyperparameter values of `max_models` and `max_models_per_type`.
- In order to know those hyperparameter values, I need the hyperparameters initialized.
- `self._init_params()` initializes the parameters so I can use them in `self._preprocess_set_features`.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
