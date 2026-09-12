# GH451_TileOPs_296: [BugFix][NSA] Fix missing loop_start in gqa_window_sliding KV loop — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/tile-ai/TileOPs/issues/295
- Repo: https://github.com/tile-ai/TileOPs

## Issue Description

## Problem

After PR #292 fixed the negative `loop_range` bug (when `offset < 0`), `test_nsa_gqa_window_sliding_op` still fails intermittently on a **different test case**:

```
FAILED tests/ops/test_deepseek_nsa_gqa_window_sliding.py::test_nsa_gqa_window_sliding_op[1-16-1024-1024-64-128-True-32--1-dtype0-accum_dtype0-False]
AssertionError: not close, max err: 6.16015625
```

Parameters: `batch_size=1, groups=16, uq=1024, ukv=1024, heads=64, dim=128, is_causal=True, window_size_left=32, window_size_right=-1`.

**PR #292's clamp has no effect here** because `offset = kv_seqlen - q_seqlen = 0` — `max_visible_k_idx` is never negative.

### Root Cause

The KV loop in `tileops/kernels/deepseek_nsa/gqa_window_sliding.py:87-95` computes the causal **upper** bound (`loop_range`) but always starts at `k=0`, ignoring the sliding-window **lower** bound.

With `window_size_left=32` and `block_n=128`, for Q block `bx=7` (positions 896-1023):

| Loop iter k | KV positions | Visible to any Q in block? | Status |
|---|---|---|---|
| k=0 | 0-127 | No (all < 864) | Wasted — fully masked by window |
| k=1 | 128-255 | No | Wasted |
| k=2 | 256-383 | No | Wasted |
| k=3 | 384-511 | No | Wasted |
| k=4 | 512-639 | No | Wasted |
| k=5 | 640-767 | No | Wasted |
| k=6 | 768-895 | Yes (864-895 visible) | Partially masked |
| k=7 | 896-1023 | Yes | Partially masked |

**6 of 8 iterations process fully-masked KV blocks**, relying on `-1e9` masking + `scores_scale = 0.0` to zero out the accumulated garbage at the transition to real blocks.

### Why this causes intermittent failures

In these fully-masked iterations, every `acc_s` entry is pre-filled with `-1e9`, then GEMM adds `Q*K^T`. The online softmax computes:

```
exp2(acc_s[i,j] * scale - scores_max[i] * scale)
```

Both terms ≈ `-1.276e8`, with float32 ULP = 8 at this magnitude. The subtraction loses all significant digits of the actual QK difference (catastrophic cancellation), producing a near-uniform softmax distribution instead of zeros.

In theory, `scores_scale = exp2(-1.276e8) = 0.0` (exact in IEEE 754 float32) should zero everything when real blocks appear. In practice, three factors make this fragile:

1. **`TL_ENABLE_FAST_MATH: True`** (line 31) — CUDA fast math uses approximate `exp2`, relaxed rounding, and FMA fusion that can change intermediate precision at the `-1.276e8` magnitude.
2. **`T.Pipelined` with dual `T.copy`** — K copy at loop top (pipelined) and V copy mid-body (synchronous). With `num_stages=2`, any synchronization gap between the two can cause stale shared memory reads, data-dependently.
3. **6 iterations of garbage accumulation** — Large `logsum` (~768) and `acc_o` values that must be multiplied by exactly `0.0` to vanish. Any imprecision leaks as corrupted output.

### Contrast with `flash_attn/fwd.py`

The flash attention forward kernel (`tileops/kernels/flash_attn/fwd.py:65-74`) avoids this entirely:
- Uses **`-T.infinity(acc_s.dtype)`** for masking (not `-1e9`)
- Uses **tight causal loop bounds** — `loop_range = ceildiv((bx+1)*block_m, block_n)` — so no fully-masked iterations occur

The `gqa_window_sliding` kernel cannot use `-T.infinity()` directly because fully-masked blocks would cause `exp2(-inf - (-inf)) = NaN`. The correct solution is to also add tight loop bounds.

## Proposed Fix

Compute a window-aware `loop_start` to skip blocks entirely outside the window:

```python
# Current (line 87-95):
if is_causal:
    max_visible_k_idx = T.max(offset + (bx + 1) * block_m, 0)
    loop_range = T.min(
        T.ceildiv(max_visible_k_idx, block_n),
        T.ceildiv(kv_current_seqlen, block_n))

for k in T.Pipelined(loop_range, num_stages=num_stages):
    # k always starts at 0

# Proposed:
if is_causal:
    max_visible_k_idx = T.max(offset + (bx + 1) * block_m, 0)
    loop_end = T.min(
        T.ceildiv(max_visible_k_idx, block_n),
        T.ceildiv(kv_current_seqlen, block_n))
else:
    loop_end = T.ceildiv(kv_current_seqlen, block_n)

# NEW: window-aware start
if has_window and window_size_left >= 0:
    min_visible_kv = T.max(offset + bx * block_m - window_size_left, 0)
    loop_start = min_visible_kv // block_n
else:
    loop_start = 0

loop_count = T.max(loop_end - loop_start, 0)

for k_offset in T.Pipelined(loop_count, num_stages=num_stages):
    k = k_offset + loop_start  # actual KV block index
    # ... rest of loop body uses k ...
```

For the failing case (`bx=7, window=32, block_n=128`): `loop_start = 864 // 128 = 6`, `loop_count = 2`. Only k=6 and k=7 are processed — zero wasted iterations, zero risk of catastrophic cancellation.

**Secondary hardening:** After adding `loop_start`, change `-1e9` to `-T.infinity(accum_dtype)` to match `flash_attn/fwd.py` semantics. With `loop_start` preventing fully-masked iterations, `-inf` is safe.

## Expected Impact

- Fixes intermittent CI failure on `test_nsa_gqa_window_sliding_op` for all parameter combinations
- Performance improvement: skips unnecessary GEMM operations on fully-masked KV blocks (up to `(seq_len / block_n - 1)` iterations saved for small windows)

## To Reproduce

```bash
for i in $(seq 1 20); do
  pytest -xvs tests/ops/test_deepseek_nsa_gqa_window_sliding.py \
    -k "1-16-1024-1024-64-128-True-32" 2>&1 | tail -5
done
```

## Next Steps

A PR will follow with the `loop_start` implementation and optional `-1e9` → `-T.infinity()` change.

## Related

- Closes #291 (partially — PR #292 fixed one trigger, this addresses the remaining one)
- PR #292: [BugFix][NSA] Fix negative loop_range in causal gqa_window_sliding

## PR Review Comments

**[user]** on `tileops/kernels/deepseek_nsa/gqa_window_sliding.py`:

![high](https://www.gstatic.com/codereviewagent/high-priority.svg)

It's crucial to ensure that `loop_count` is always non-negative to prevent potential issues with the `T.Pipelined` iterator. If `loop_count` is negative, it could lead to unexpected behavior or errors during kernel execution. Consider adding an assertion or a check to ensure `loop_count >= 0` before entering the loop.

**[user]** on `tileops/kernels/deepseek_nsa/gqa_window_sliding.py`:

![medium](https://www.gstatic.com/codereviewagent/medium-priority.svg)

The comment is helpful, but it would be more informative to include the specific condition under which this optimization is applied (e.g., when `has_window` is true and `window_size_left` is non-negative).

**[user]** on `tileops/kernels/deepseek_nsa/gqa_window_sliding.py`:

![medium](https://www.gstatic.com/codereviewagent/medium-priority.svg)

Renaming `k` to `k_offset` improves readability by clearly indicating that this variable represents an offset within the loop. This change enhances the code's self-documentation.

**[user]** on `tileops/kernels/deepseek_nsa/gqa_window_sliding.py`:

![medium](https://www.gstatic.com/codereviewagent/medium-priority.svg)

The variable `k` is computed inside the loop, which is good for reflecting the offset-based iteration. However, it might be more efficient to precompute `kv_start_idx + k * block_n` outside the inner loop since `kv_start_idx`, `k`, and `block_n` are loop invariants. This could reduce redundant calculations within the loop.

**[user]** on `tileops/kernels/deepseek_nsa/gqa_window_sliding.py`:

![medium](https://www.gstatic.com/codereviewagent/medium-priority.svg)

The current implementation copies data from `k_unpad` to `k_shared` within the pipelined loop. This could introduce a performance bottleneck due to memory access overhead. Consider exploring alternative strategies, such as prefetching or double-buffering, to mitigate the impact of memory latency and improve overall performance.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
