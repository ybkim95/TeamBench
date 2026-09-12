# GH1094_spaCy_12575: Add spans in spacy benchmark — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/explosion/spaCy

## PR Description

This PR attempts to fix that by creating a new parameter for "spans" and calling the appropriate displaCy value.


## Description

#12566 

The current implementation of spaCy benchmark accuracy / spacy evaluate doesn't include the "spans" type, so calling the command doesn't render the HTML displaCy file needed. The reason why it wasn't included in the first place was *probably* because the "spans" feature in displaCy is relatively new.

### Types of change

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
