# GH366_boto3_4613: Fix ExtraArgs documentation in S3 copy methods to reference ALLOWED_COPY_ARGS — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/boto/boto3

## PR Description

Fixes incorrect documentation in S3 copy method that reference `ALLOWED_DOWNLOAD_ARGS` instead of `ALLOWED_COPY_ARGS`.

## Changes
- Updated `boto3/s3/inject.py` for `copy()`, `bucket_copy()`, and `object_copy()` methods
- Changed references from `ALLOWED_DOWNLOAD_ARGS` to `ALLOWED_COPY_ARGS`
- Updated text from "download arguments" to "copy arguments"
- Updated `boto3/s3/transfer.py` to have `ALLOWED_COPY_ARGS = TransferManager.ALLOWED_COPY_ARGS` under `class S3Transfer`

## Issue
Resolves documentation inconsistency reported in #3163 where copy operations incorrectly documented supported ExtraArgs.

## Files Changed
- `boto3/s3/inject.py`

The actual s3transfer implementation supports `ALLOWED_COPY_ARGS` but the boto3 documentation was incorrectly referencing `ALLOWED_DOWNLOAD_ARGS`, causing confusion about which arguments are supported for copy operations.

## Before:
<img width="719" height="889" alt="Screenshot 2025-09-10 at 4 17 05 PM" src="https://github.com/user-attachments/assets/0ef05d13-98dc-4f90-bba6-1538dd7580ca" />

<img width="776" height="768" alt="Screenshot 2025-09-10 at 4 17 17 PM" src="https://github.com/user-attachments/assets/20a6a150-01d1-4a21-9030-b92d62a4a323" />

## After:
<img width="813" height="943" alt="Screenshot 2025-09-10 at 4 06 28 PM" src="https://github.com/user-attachments/assets/216ff165-ffa8-44fd-a38d-6c2e1582894e" />

<img width="847" height="909" alt="Screenshot 2025-09-10 at 4 06 51 PM" src="https://github.com/user-attachments/assets/89b3fb20-3ea8-4272-a2e8-45812a95dccf" />

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
