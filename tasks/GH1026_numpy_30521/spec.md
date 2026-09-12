# GH1026_numpy_30521: BUG: validate contraction axes in tensordot — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/numpy/numpy

## PR Description

tensordot performs a tensor contraction where each axis corresponds to a distinct summation index. Duplicate contraction axes (e.g. axes=([1, 1], [0, 0])) are mathematically invalid but currently fail later during an internal transpose, raising ValueError: axes don't match array. This PR adds early validation to reject duplicate axes explicitly, aligning the behavior with the definition of tensor contraction and other NumPy axis-handling APIs.

Current behavior:
Supplying duplicate contraction axes (e.g. axes=([1, 1], [0, 0])) causes tensordot to fail later during an internal transpose, raising ValueError: axes don't match array.

Expected behavior:
Duplicate contraction axes should be rejected explicitly, since tensor contraction requires distinct summation axes, and a clear input-validation error should be raised before any internal reshaping or transposition.

<!--         ----------------------------------------------------------------
                MAKE SURE YOUR PR GETS THE ATTENTION IT DESERVES!
                ----------------------------------------------------------------

*  FORMAT IT RIGHT:
      https://www.numpy.org/devdocs/dev/development_workflow.html#writing-the-commit-message

*  IF IT'S A NEW FEATURE OR API CHANGE, TEST THE WATERS:
      https://www.numpy.org/devdocs/dev/development_workflow.html#get-the-mailing-list-s-opinion

*  HIT ALL THE GUIDELINES:
      https://numpy.org/devdocs/dev/index.html#guidelines

*  WHAT TO DO IF WE HAVEN'T GOTTEN BACK TO YOU:
      https://www.numpy.org/devdocs/dev/development_workflow.html#getting-your-pr-reviewed
-->

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
