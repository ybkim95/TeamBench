# GH1111_keras_20774: fix(ops): Fix inconsistent padding calculation in PyTorch backend ops — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/keras-team/keras

## PR Description

→ Was able to still reproduce the error, the PyTorch backend had inconsistent behavior between static shape inference and dynamic execution for pooling operations, particularly with 'same' padding and non-unit strides, figured that the root cause was by incorrect padding calculation logic that didn't properly handle asymmetric padding cases.

**Key changes:**

→ Rewrote `_compute_padding_length()` to handle stride-based padding
→ Fixed padding calculation to properly support asymmetric padding cases
→ Standardize `channels_first`/`channels_last` conversion in pooling ops
→ Cleaned up padding application in `_apply_same_padding()`
→ Added proper handling of `data_format` throughout pooling pipeline

→ This fixes the issue where MaxPooling2D with 'same' padding would produce different shapes between compute_output_shape() and actual execution (e.g. (1,5,2,2) vs (1,5,2,1)) #20235.

Rebased on top of [user]'s September 2024 PR to incorporate latest `keras:master` changes #20270

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
