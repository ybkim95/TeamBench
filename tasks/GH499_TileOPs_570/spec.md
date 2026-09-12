# GH499_TileOPs_570: [Fix][Elementwise] Handle MaskedFill overflow fill_value for fp16 output dtype — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/tile-ai/TileOPs/issues/569
- Repo: https://github.com/tile-ai/TileOPs

## Issue Description

## Description

`test_masked_fill_e5m2_overflow_fill_value` fails on CI (`gpu-smoke` job, [run](https://github.com/tile-ai/TileOPs/actions/runs/23238669568/job/67549108935)) because `T.cast(100000, "float16")` triggers a TVM `FloatImm` range check:

```
tvm.error.InternalError: Check failed: value <= support::kMaxFloat16 (100000 vs. 65504)
```

For e5m2 masked_fill, the kernel outputs float16 (Op layer does the final non-saturating cast to e5m2). When `fill_value` exceeds float16 max finite (65504), TVM rejects the literal — even though inf is a valid float16 value. This is a TVM limitation in `FloatImm` construction. Introduced in #549.

## Goal

Fix `_make_masked_fill_kernel` so that overflow fill values (producing inf in float16) are handled correctly, without triggering TVM's `FloatImm` range check.

## Plan
<!-- type: fixed -->

1. Add `_fill_value_overflows_fp16()` helper to detect overflow at kernel build time
2. In `_make_masked_fill_kernel`, when overflow is detected, construct inf via `T.reinterpret(T.cast(0x7C00, "uint16"), "float16")` instead of `T.cast(fill_value, out_dtype)`
3. Apply the fix to both fp8 and non-fp8 code paths

## Constraints

- Must not regress existing elementwise fp8 tests
- Must not change kernel interface or Op layer behavior

## Acceptance Criteria

- [ ] `test_masked_fill_e5m2_overflow_fill_value` passes
- [ ] All existing `test_elementwise_independent_fp8.py` tests pass
- [ ] All existing `test_elementwise_fp8.py` tests pass
- [ ] Fix applies to both fp8 and non-fp8 code paths in `_make_masked_fill_kernel`

## PR Review Comments

**[user]** on `tileops/kernels/elementwise.py`:

![medium](https://www.gstatic.com/codereviewagent/medium-priority.svg)

This logic for determining `fv` is duplicated from the `is_fp8` branch (lines 2369-2374). To improve maintainability and avoid repetition, you could define a helper lambda before the `if is_fp8:` block.

For example:
```python
get_fv_expr = lambda T, target_dtype: (
    T.reinterpret(T.cast(_fp16_inf_bits, "uint16"), "float16")
    if _fp16_fill_is_inf
    else T.cast(fill_value, target_dtype)
)
```
Then you can call `fv = get_fv_expr(T, out_dtype)` in the `is_fp8` kernel and `fv = get_fv_expr(T, dtype)` in this one, removing the `if/else` block from both kernel definitions.

**[user]** on `tileops/kernels/elementwise.py`:

![medium](https://www.gstatic.com/codereviewagent/medium-priority.svg)

To improve readability and maintainability, consider defining the hexadecimal values for float16 infinity as named constants instead of using magic numbers directly.

```python
    _FP16_POS_INF_BITS = 0x7C00
    _FP16_NEG_INF_BITS = 0xFC00
    _fp16_inf_bits = (_FP16_NEG_INF_BITS if fill_value < 0 else _FP16_POS_INF_BITS) if _fp16_fill_is_inf else 0
```

**[user]** on `tileops/kernels/elementwise.py`:

`numpy` is newly imported but the project dependencies in `pyproject.toml` don’t include numpy. This will cause a runtime `ModuleNotFoundError` for users/installations that only install the declared dependencies. Consider removing the numpy usage (e.g., use `torch.finfo(torch.float16).max`/`math.isfinite` to detect overflow) or explicitly adding numpy as a required dependency.

**[user]** on `tileops/kernels/elementwise.py`:

The helper’s docstring says it returns True when `fill_value` “exceeds float16 finite range”, but the implementation also returns True when `fill_value` is already `+/-inf` (since `np.float16(inf)` is inf). Consider clarifying the docstring to match the actual behavior (e.g., “casts to float16 as inf”).

**[user]** on `tileops/kernels/elementwise.py`:

Accepted. Replaced `numpy` with `math.isinf` + `abs(fill_value) > 65504.0` — no new dependency needed. See 6c5df18.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
