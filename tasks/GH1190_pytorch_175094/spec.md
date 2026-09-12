# GH1190_pytorch_175094: Revert "[fix] DISABLED test_index (__main__.DistTensorOpsTest) (#172373)" — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pytorch/pytorch

## PR Description

This reverts commit 70726364e8565902d6f9ed9e47cd197caf544399.

Reverted (withheld: the upstream fix is not part of the task) on behalf of https://github.com/[user] due to PR claims to fix ROCm DISABLED issue but it did not ([comment]((withheld: the upstream fix is not part of the task)#issuecomment-3909564537))

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
