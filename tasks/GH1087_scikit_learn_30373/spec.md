# GH1087_scikit_learn_30373: API drop Tags.regressor_tags.multi_label — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/scikit-learn/scikit-learn

## PR Description

Follow-up on #29677 discovered while reviewing #30187.

Let's remove the field `tags.regressor_tags.multi_label` because:

- it's meaningless;
- it's redundant with `tags.target_tags.multi_output` automatically set by `MultioutputMixin` for regressors;
- it does not map to any concept document in our glossary.

Note that the bug was already present in `ForestRegressor._more_tags` before #29677, but since 1.6 is not released yet, let's fix this before making it officially part of our new Tag API.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
