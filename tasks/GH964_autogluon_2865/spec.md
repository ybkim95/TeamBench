# GH964_autogluon_2865: Tabular: Fix error when loading with a different OS — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/autogluon/autogluon

## PR Description

*Issue #, if available:*
#2208

*Description of changes:*
Fixes exception during load when TabularPredictor was trained on Windows, and then loaded on MacOS/Linux.
Should also fix exception when trained on MacOS/Linux and loaded on Windows.

Because this PR introduces a new check on load based on a new variable, prior trained predictors on earlier versions will not be able to load using this PR.

**Note**: I have not formally tested this yet as I don't have a Windows machine on hand. Would appreciate if those affected can comment on if this PR fixes their problem.

Follow-up: Add unit test, tracked in #2863


By submitting this pull request, I confirm that you can use, modify, copy, and redistribute this contribution, under the terms of your choice.

## PR Review Comments

**[user]** on `tabular/src/autogluon/tabular/models/fastainn/tabular_nn_fastai.py`:

Wouldn't we need to update this back to pathlib.WindowsPath after the load?

**[user]** on `tabular/src/autogluon/tabular/models/fastainn/tabular_nn_fastai.py`:

Good call. Updated

**[user]** on `common/src/autogluon/common/utils/path_converter.py`:

Can we add a unit test for each of these functions?

**[user]** on `common/tests/unittests/test_path_converter.py`:

We should add a unit test for the absolute path example both from linux and windows

https://learn.microsoft.com/en-us/dotnet/standard/io/file-path-formats

For example, on windows it could be something like:

"C:\Documents\foo\"

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
