# GH1204_evaluate_230: Fix enforce string — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/huggingface/evaluate

## PR Description

Some casting operations throw `ValueError`s while others `TypeError`s. With this PR both are cought when inferring the type to make sure the iterative testing of feature types doesn't get interrupted. We didn't catch this so far because we had `Sequence` first and `str` second. I updated the test to include both cases, which would fail before and passes now.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
