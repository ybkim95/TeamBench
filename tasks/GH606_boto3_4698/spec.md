# GH606_boto3_4698: Updated SourceClient documentation — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/boto/boto3

## PR Description

Updated SourceClient documentation to clarify that the client still needs IAM permissions to access both buckets.

*Issue #, if available:*

N/A, internal ticket

*Description of changes:*

Added "The current client still requires IAM permissions to access both buckets."  to all SourceClient documentation.

By submitting this pull request, I confirm that you can use, modify, copy, and redistribute this contribution, under the terms of your choice.

## PR Review Comments

**[user]** on `boto3/s3/inject.py`:

nit - I think swapping the order of these sentences makes more sense. Reading `The current client still requires IAM permissions to access both buckets.` seems weird to be brought up before `If no client is provided, the current client is used as the client for the source object.`. We are only talking about the former because of the later so I think it make sense to swap. 

Let me know what you think

**[user]** on `boto3/s3/inject.py`:

Makes sense.  I've swapped the sentence order, removed the trailing whitespace, and added a `s` to `operation`.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
