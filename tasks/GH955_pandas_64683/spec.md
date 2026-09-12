# GH955_pandas_64683: BUG: fix sum of empty series for python-backed str dtype and account for min_count — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pandas-dev/pandas

## PR Description

See (withheld: the upstream fix is not part of the task)#discussion_r2952141511 for context

- [x] [Tests added and passed](https://pandas.pydata.org/pandas-docs/dev/development/contributing_codebase.html#writing-tests) if fixing a bug or adding a new feature
- [x] All [code checks passed](https://pandas.pydata.org/pandas-docs/dev/development/contributing_codebase.html#pre-commit).
- [x] Added an entry in the latest `doc/source/whatsnew/vX.X.X.rst` file if fixing a bug or adding a new feature.

## PR Review Comments

**[user]** on `pandas/core/array_algos/masked_reductions.py`:

suggestion: Would be good to update this docstring with `initial`

**[user]** on `pandas/core/array_algos/masked_reductions.py`:

Good point! Updated

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
