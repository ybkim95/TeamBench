# GH1218_featuretools_2030: Woodwork version 0.16 fixes — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/alteryx/featuretools

## PR Description

Updates for compatibility for WW version 0.16

- bump min WW requirement to 0.16.1
- Update serialization to specify filename when deserializing from parquet
- Fix test in `test_transform_features.py`

## PR Review Comments

**[user]** on `featuretools/entityset/serialize.py`:

i think if we're unable to deserialize an entityset parquet serialized with schema version 7.0.0 we should consider this a breaking change and bump schema version to 8.0.0

**[user]** on `featuretools/entityset/serialize.py`:

Updated

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
