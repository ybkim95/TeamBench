# GH1150_FLAML_1494: Fix nested dictionary merge in SearchThread losing sampled hyperparameters — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/microsoft/FLAML/issues/1246
- Repo: https://github.com/microsoft/FLAML

## Issue Description

<!-- Thank you for your contribution! Please review https://microsoft.github.io/FLAML/docs/Contribute before opening a pull request. -->

<!-- Please add a reviewer to the assignee section when you create a PR. If you don't have the access to it, we will shortly find a reviewer and assign them to your PR. -->

## Why are these changes needed?
Reference to https://github.com/microsoft/FLAML/issues/1244

<!-- Please give a short summary of the change and the problem this solves. -->

## Related issue number
https://github.com/microsoft/FLAML/issues/1244

<!-- For example: "Closes #1234" -->

## Checks

<!-- - I've used [pre-commit](https://microsoft.github.io/FLAML/docs/Contribute#pre-commit) to lint the changes in this PR (note the same in integrated in our CI checks). -->
- [ ] I've included any doc changes needed for https://microsoft.github.io/FLAML/. See https://microsoft.github.io/FLAML/docs/Contribute#documentation to build and test documentation locally.
- [ ] I've added tests (if relevant) corresponding to the changes introduced in this PR.
- [ ] I've made sure all auto checks have passed.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Any follow up on this please? The PR looks ready.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
