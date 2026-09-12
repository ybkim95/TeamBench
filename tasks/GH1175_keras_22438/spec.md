# GH1175_keras_22438: Fix Inconsistent tensor conversion — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/keras-team/keras

## PR Description

- Convert L2.l2 to tensor in __init__ via ops.convert_to_tensor() to match L1 behavior, avoiding repeated implicit float-to-tensor conversion on every forward pass

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
