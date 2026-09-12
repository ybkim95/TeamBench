# GH1072_spaCy_13321: Make `Language.pipe` workers exit cleanly — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/explosion/spaCy

## PR Description

<!--- Provide a general summary of your changes in the title. -->

## Description
<!--- Use this section to describe your changes. If your changes required
testing, include information about the testing environment and the tests you
ran. If your test fixes a bug reported in an issue, don't forget to include the
issue number. If your PR is still a work in progress, that's totally fine – just
include a note to let us know. -->

Also warn when any worker exited with a non-zero exit code and modify test to ensure that workers exit cleanly by default.

### Types of change
<!-- What type of change does your PR cover? Is it a bug fix, an enhancement
or new feature, or a change to the documentation? -->

Bugfix

## Checklist
<!--- Before you submit the PR, go over this checklist and make sure you can
tick off all the boxes. [] -> [x] -->
- [x] I confirm that I have the right to submit this contribution under the project's MIT license.
- [x] I ran the tests, and all new and existing tests passed.
- [x] My changes don't require a change to the documentation, or if they do, I've added all required information.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
