# GH1035_autogluon_5475: [timeseries] fixes to Toto and add to smoke tests — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/autogluon/autogluon

## PR Description

*Issue #, if available:*

*Description of changes:*

- disables compilation by default in Toto, for added stability
- computes inference batch size dynamically (previous logic forced batch size to be multiple of 32)
- add to smoke tests


By submitting this pull request, I confirm that you can use, modify, copy, and redistribute this contribution, under the terms of your choice.

## PR Review Comments

**[user]** on `timeseries/tests/smoketests/test_all_models.py`:

Maybe we can keep this even lower for better efficiency? Like `"num_samples": 5"` even

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
