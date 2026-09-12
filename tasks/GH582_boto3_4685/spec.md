# GH582_boto3_4685: Fix flaky integration tests from resource name collisions — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/boto/boto3

## PR Description

*Issue #, if available:*
N/A

*Description of changes:*
This PR updates `unique_id()` to generate resource names using UUIDs instead of a timestamp + random integer. The previous approach could produce collisions when integration tests run in parallel, which occasionally led to `ResourceInUseException` errors (in `test_dynamodb.py`)when creating resources that were already in the process of being created.

By submitting this pull request, I confirm that you can use, modify, copy, and redistribute this contribution, under the terms of your choice.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
