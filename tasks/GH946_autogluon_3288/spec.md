# GH946_autogluon_3288: Tabular: Fix crash when save path is absolute — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/autogluon/autogluon

## PR Description

*Issue #, if available:*

*Description of changes:*
- If using an absolute path in predictor init, will crash upon load.

This PR fixes the obvious error so that the below script works, however the current fix is not a good idea long-term, as I have no idea if there will be edge-cases where it fails. I also don't know if it will work when using multiple disk drives in a single process.

The root of the issue is that `StackerEnsembleModel` does something it shouldn't: It has the absolute paths of both itself and its base models stored as variables. Therefore, in order to figure out where the base models are upon loading in a new location, it isn't sufficient to look at the old absolute paths, instead they need to be regenerated based on 1. the old absolute path, 2. the new path.

For example:

```
Model 1: `/abc/def/`
Model 2: `./foo/bar/`


# Model 1 where model 2 is a base model:
self.path_root = `/abc/def/`
self.base_model_paths_dict = {
    'model_2': './foo/bar/'
}
```

When loaded from a new location, this can cause issues. It worked in the past except for cross-os loading.

```
new_path = './new/location/'
new_model_2_path = ?????  # <------- This is the problem, hard to figure out the correct path
```

The solution is to either

1. Delete StackerEnsembleModel and have `trainer` deal with this (Ideal, but significant work)
2. Convert absolute paths to relative paths, or otherwise hack things to avoid the breaking situation (What I've done in this PR, but I don't like it. It **probably** fixes things, but hard to know for sure in all cases).
3. Bandaid solution by try/except on the path conversion: If can't convert because absolute, assume same machine and continue (will crash if cross-OS and absolute path was used during fit).

Reproducible Example:
```python3
from autogluon.tabular import TabularPredictor, TabularDataset


if __name__ == '__main__':
    data_root = 'https://autogluon.s3.amazonaws.com/datasets/Inc/'
    train_data = TabularDataset(data_root + 'train.csv')
    train_data = train_data.sample(500)
    test_data = TabularDataset(data_root + 'test.csv')

    predictor = TabularPredictor(
        label='class',
        path='/tmp/tmpfe_o0p7g/',
    ).fit(
        train_data=train_data,
        hyperparameters={'DUMMY': {}},
        fit_weighted_ensemble=False,
        num_bag_folds=2,
        num_bag_sets=1,
    )
    predictor.persist_models('best')
    predictor.leaderboard(test_data)
```

Exception:
```
    assert not PathConverter._is_absolute(path), "It is ambiguous on how to convert an absolute path. Please provide a relative path instead"
AssertionError: It is ambiguous on how to convert an absolute path. Please provide a relative path instead
```


By submitting this pull request, I confirm that you can use, modify, copy, and redistribute this contribution, under the terms of your choice.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
