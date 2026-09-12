# GH1039_darts_2776: Fix/categorical validation features — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/unit8co/darts

## PR Description

Checklist before merging this PR:
- [x] Mentioned all issues that this PR fixes or addresses.
- [x] Summarized the updates of this PR under **Summary**.
- [x] Added an entry under **Unreleased** in the [Changelog](../CHANGELOG.md).

<!-- Please mention an issue this pull request addresses. -->
Fixes #.

### Summary

<!-- Provide a general description of the code changes in your pull
request. If your pull request is not ready to merge, please create
a draft and ask for comments. -->

Validation set was not formated to support categorical features.
`CatBoost` requires the `cat_features` to be specified in the validation `Pool` in case of categorical features in validation set.


### Other Information

<!-- If there's anything else that's important and relevant to your pull
request, mention that information here. This could include
benchmarks, code samples, or others. -->

<!--Thank you for contributing to darts! -->

## PR Review Comments

**[user]** on `darts/tests/models/forecasting/test_regression_models.py`:

```suggestion
                # all evals set have correct cat feature indices
```

**[user]** on `darts/models/forecasting/regression_model.py`:

Nice!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
