# GH1001_numpy_30855: BUG: fix infinite recursion in np.ma.flatten_structured_array — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/numpy/numpy

## PR Description

Towards resolving #29349 

Avoids recursion for both strings and objects.

## PR Review Comments

**[user]** on `numpy/ma/core.py`:

If we do this minimal thing, I am tempted to just add `not isinstance(elem, (str, bytes))`, TBH.
`np.ndim()` may be slow and I don't consider this the true fix either way, so I am probably more happy with a practical 98% fix than something that looks like a neat fix but isn't really.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
