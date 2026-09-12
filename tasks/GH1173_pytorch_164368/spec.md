# GH1173_pytorch_164368: [Flex attention] Fix flex attention head broadcast — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pytorch/pytorch

## PR Description

Fixes part of #163314

In particular bug: **Bug 1: H=None Broadcasting Produces Incorrect Results**

This fixes a shape bug when slicing BlockMask on the Q-tile axis with an int (**mask[:, :, i]**). That form of indexing collapses the Q dimension, so kv_num_blocks/kv_indices lose their expected [B, H, Q_tiles, …] shape. Due to them losing shape, even though the mask_mod remains "interpretable", the kernel’s stride math then reads wrong offsets. Due to this we get silent numerical mismatches compared to regular SDPA, especially when single position decoding/H broadcasting.

The B=None, H=None works case is accidental: with singleton batch/head the kernel maps to index 0 via `sparse_idx_z = off_zq % 1` and `sparse_idx_hq = off_hq % 1` and with a single Q tile `q_start // SPARSE_Q_MULTIPLE = 0`. The missing Q-tiles stride is multiplied by 0, so the bad offset from the collapsed Q axis doesn’t move the pointer and it happens to read the first tile correctly. Once H > 1 or there are multiple Q tiles, those terms become nonzero and the kernel indexes with wrong strides which causes silent error

cc [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user] [user]

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
