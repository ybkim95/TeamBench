# GH935_spaCy_7026: Fix issue #7019: Handle None scores in evaluate printer — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/explosion/spaCy

## PR Description

<!--- Provide a general summary of your changes in the title. -->

## Description

Only try to pretty-print actual numbers and don't error on `None` scores in `evaluate` printer.

### Types of change
<!-- What type of change does your PR cover? Is it a bug fix, an enhancement
or new feature, or a change to the documentation? -->

## Checklist
<!--- Before you submit the PR, go over this checklist and make sure you can
tick off all the boxes. [] -> [x] -->
- [x] I have submitted the spaCy Contributor Agreement.
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
