# GH953_scikit_learn_20853: Fix OvOClassifier.n_features_in_ and other unexpected warning at prediction time when checking feature_names_in_ — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/scikit-learn/scikit-learn

## PR Description

## Reference Issues/PRs

Follow up to #18010

## What does this implement/fix? Explain your changes.

Add a new test to make sure that we do not raise an expected warning when checking the input data at prediction time, notably in meta-estimators: if the data is validated by the meta estimator at fit time, it should also be validated by the meta-estimator at predict time. The base estimator should therefore not receive a dataframe with column names at predict time.

## PR Review Comments

**[user]** on `sklearn/tests/test_common.py`:

There was nothing left to do here apparently.

**[user]** on `sklearn/linear_model/_ransac.py`:

While this was not strictly required to have the new test pass, it's an optim to avoid redundant finiteness check with the base estimator fit method.

**[user]** on `sklearn/semi_supervised/_self_training.py`:

Same comment here for `force_all_finite=False`.

There are probably other meta-estimators that could benefit from a similar treatment.

**[user]** on `sklearn/ensemble/_forest.py`:

This check is the equivalent to `self.estimators_[0]._validate_X_predict(X, check_input=True)` but this avoid having calling `self.estimators_[0]._validate_data(X, reset=False)` with X being a dataframe only at predict time which would cause the "was fitted without feature names"-warning to be raised.

**[user]** on `sklearn/multiclass.py`:

This was actually causing a bug in `OvOClassifier` when X is a pre-computed kernel:

The number of features for the OvO meta-estimator is larger than the number of features of base estimators because when we do OvO, we remove the samples of the classes we are not interested in, and therefore the number of "features" since the columns of a precomputed kernel matrix `X` are actually samples, not features.

This bug was previously silent but started to break once I fixed the predict time validation to silence the warning. I will try to write a dedicated test and probably document the fix in a changelog entry.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
