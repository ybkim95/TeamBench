# GH1192_pytorch_171129: [Inductor] Fix constants handling for Triton constexpr (triton#8248) (Brief)

Fix the bug described by the Planner's guidance in the workspace.

## Verification

Run the test suite to confirm your fix:

```
pytest test/inductor/test_triton_kernels.py -x -q
```

Do NOT modify test files.

Follow the Planner's guidance precisely.
