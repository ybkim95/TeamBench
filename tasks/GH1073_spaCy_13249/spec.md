# GH1073_spaCy_13249: `TextCatParametricAttention.v1`: set key transform dimensions — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/explosion/spaCy

## PR Description

This is necessary for tok2vec implementations that initialize lazily (e.g. curated transformers).

<!--- Provide a general summary of your changes in the title. -->

## Description
<!--- Use this section to describe your changes. If your changes required
testing, include information about the testing environment and the tests you
ran. If your test fixes a bug reported in an issue, don't forget to include the
issue number. If your PR is still a work in progress, that's totally fine – just
include a note to let us know. -->

Set key transform dimensions in `TextCatParametricAttention.v1`, otherwise the key transformation dimensionality cannot be inferred for lazily-initialized tok2vecs listeners like transformers.

Not sure how we can test this without making a new tok2vec model in spaCy that is lazily initialized (does know its width until initialization). Maybe we should add a separate model to the tests?

### Types of change
<!-- What type of change does your PR cover? Is it a bug fix, an enhancement
or new feature, or a change to the documentation? -->

## Checklist
<!--- Before you submit the PR, go over this checklist and make sure you can
tick off all the boxes. [] -> [x] -->
- [x] I confirm that I have the right to submit this contribution under the project's MIT license.
- [x] I ran the tests, and all new and existing tests passed.
- [x] My changes don't require a change to the documentation, or if they do, I've added all required information.

## PR Review Comments

**[user]** on `spacy/tests/tok2vec.py`:

Maybe we should add a "test." prefix just to be fully clear this isn't meant to be used in any way?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
