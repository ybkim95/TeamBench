# GH1137_pytorch_171247: [xpu][fix][inductor] fallback bfloat16 atomics to eager — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pytorch/pytorch/issues/170756
- Repo: https://github.com/pytorch/pytorch

## Issue Description

### 🐛 Describe the bug

(withheld: the upstream fix is not part of the task) this pr causes regression on beit_base_patch16_224 and basic_gnn_gin, we should fallback bf16 atomic to eager

### Versions

2.10

cc [user] [user] [user] [user]

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
