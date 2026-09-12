# GH1192_pytorch_171129: [Inductor] Fix constants handling for Triton constexpr (triton#8248) — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pytorch/pytorch

## PR Description

Up until recently (triton-lang/triton#8248), Triton did not explicitly interpret entries in `ASTSource.constants` , and Inductor historically treated  "non-tensor-like" arguments as `constexpr`, including runtime scalars. Triton’s updated `constexpr` handling now requires stricter semantics, so this change restricts `constants` to arguments marked `is_constexpr` rather than all “non-tensor-like” arguments.

- Fixes issue #170049. 

cc [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user]

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
