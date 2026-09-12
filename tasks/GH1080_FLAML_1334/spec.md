# GH1080_FLAML_1334: fix missing req. arg for new `datasets` package — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/microsoft/FLAML

## PR Description

<!-- Thank you for your contribution! Please review https://microsoft.github.io/FLAML/docs/Contribute before opening a pull request. -->

<!-- Please add a reviewer to the assignee section when you create a PR. If you don't have the access to it, we will shortly find a reviewer and assign them to your PR. -->

## Why are these changes needed?

seems recent CI is not passing at all due to changes in the `datasets` package which now for loading requires specifying `trust_remote_code=True|False`

## Related issue number

actual state on the main branch
cc: [user]
see: https://github.com/EleutherAI/lm-evaluation-harness/issues/1135

## Checks

<!-- - I've used [pre-commit](https://microsoft.github.io/FLAML/docs/Contribute#pre-commit) to lint the changes in this PR (note the same in integrated in our CI checks). -->

- [x] I've included any doc changes needed for https://microsoft.github.io/FLAML/. See https://microsoft.github.io/FLAML/docs/Contribute#documentation to build and test documentation locally.
- [ ] I've added tests (if relevant) corresponding to the changes introduced in this PR.
- [x] I've made sure all auto checks have passed.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
