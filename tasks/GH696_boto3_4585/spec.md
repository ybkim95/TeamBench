# GH696_boto3_4585: Only pass aws_account_id to botocore when explicitly set — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/boto/boto3

## PR Description

This PR will restrict passing `aws_account_id` down to botocore unless explicitly set. This is to help minimize issues where Lambda may arbitrarily update a subset of dependencies in a customers function that can result in breaking changes.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
