# GH1012_autogluon_3480: Tabular: Fix train_test split edge-case — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/autogluon/autogluon

## PR Description

*Issue #, if available:*

*Description of changes:*

In cases where there are an extreme number of classes compared to data samples and the data is large, AutoGluon can crash during train test split due to a bug in scikit-learn's `train_test_split` function.

Example:

```
Train Data Rows:    1528329
Train Data Class Count: 27000
```

Because the test split would be 1% of the total data based on AutoGluon's split logic, it results in the test data having fewer rows than the number of classes, triggering the error:

```
ValueError: The test_size = 14915 should be greater or equal to the number of classes = 27000
```

While scikit-learn claims that test_size must be greater than the number of classes, this isn't technically required fundamentally. This PR adds a work-around for this limitation by disabling stratification during train test split if stratification would lead to the above error.


By submitting this pull request, I confirm that you can use, modify, copy, and redistribute this contribution, under the terms of your choice.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
