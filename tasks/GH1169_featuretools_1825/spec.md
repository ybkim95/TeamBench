# GH1169_featuretools_1825: Fix s3 credentials test issue — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/alteryx/featuretools

## PR Description

Some unit tests were failing to download public files if existing AWS credentials were detected

This PR shifts testing S3 deserializing with credentials to only in tests with mocked S3 fixtures, leaving the real S3 tests that do not use credentials

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
