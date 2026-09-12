# GH1149_featuretools_2380: Fix `base_of_exclude` handling — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/alteryx/featuretools/issues/2323
- Repo: https://github.com/alteryx/featuretools

## Issue Description

In `_build_transform_features` in `deep_feature_synthesis.py`, we need to handle the case where `base_of_exclude` is defined in a custom primitive. The use case for this is if the user wants to block certain primitives from stacking on other ones during feature generation.

## PR Review Comments

**[user]** on `featuretools/synthesis/deep_feature_synthesis.py`:

After discussing with [user], determined that this todo was already completed

**[user]** on `docs/source/release_notes.rst`:

```suggestion
        * Fix DeepFeatureSynthesis to consider the ``base_of_exclude`` family of attributes when creating transform features(:pr:`2380`)
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
