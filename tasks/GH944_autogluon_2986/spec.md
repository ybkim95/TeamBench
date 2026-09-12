# GH944_autogluon_2986: Fix AsTypeFeatureGenerator Edge-case Crash — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/autogluon/autogluon

## PR Description

*Issue #, if available:*

Fix bug introduced in #2944 

*Description of changes:*

- Fix bug when useless features are present (aka categorical with each value only appearing once) and boolean features >= 15, causing crash during inference in some cases.
- Technically this slows down preprocessing in this situation, but avoiding the slow down is massively complicated and not worth implementing.
- Added unit test

By submitting this pull request, I confirm that you can use, modify, copy, and redistribute this contribution, under the terms of your choice.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
