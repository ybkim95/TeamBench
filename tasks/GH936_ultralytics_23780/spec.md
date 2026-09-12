# GH936_ultralytics_23780: Fix FP16 inference crash from TinyViT cached bias dtype mismatch — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/ultralytics/ultralytics

## PR Description

## Summary

This PR fixes an FP16 inference crash in the SAM TinyViT path (e.g., `mobile_sam.pt`) caused by a dtype mismatch in cached attention bias tensors.

When `half=True`, inference can fail with:

`RuntimeError: expected scalar type Float but found Half`

## Root Cause

In `SAM` predictor setup, the model enters eval mode before dtype conversion:

- `model.eval()` triggers `train(False)` in TinyViT attention blocks.
- In `train(False)`, a cached tensor `self.ab` is created from `self.attention_biases[:, self.attention_bias_idxs]`.
- After that, `model.half()` converts parameters/buffers to FP16, but `self.ab` is a plain tensor attribute (not a parameter or registered buffer), so it remains FP32.
- During forward, `self.ab` is only moved to the right device (not dtype), which leads to mixed `Float`/`Half` matmul inputs.

## Proposed Fix

Ensure cached attention bias tensors are dtype-consistent with model weights in FP16 inference.

Implemented by:
Applying precision conversion before `eval()` in SAM predictor setup, so eval-time cache creation inherits the final dtype.

This keeps behavior unchanged for FP32 and fixes FP16 inference for TinyViT-based SAM backbones.

## Reproduction

from ultralytics import SAM

model = SAM("mobile_sam.pt")
model.predict("input/1.bmp", points=[[400, 370], [900, 370]], labels=[1, 1], half=True)

## 🛠️ PR Summary

<sub>Made with ❤️ by [Ultralytics Actions](https://www.ultralytics.com/actions)</sub>

### 🌟 Summary
Fixes an FP16 SAM inference crash by correcting model precision setup order to prevent TinyViT cached bias dtype mismatches. 🛠️⚡

### 📊 Key Changes
- Moves precision assignment (`half()`/`float()`) to occur immediately after model creation.
- Keeps evaluation mode and device transfer steps in place, while avoiding a late dtype cast that could conflict with cached TinyViT tensors.
- Updates `ultralytics/models/sam/predict.py` in `setup_model()` with a minimal, targeted change.

### 🎯 Purpose & Impact
- Prevents runtime crashes during FP16 inference for SAM setups using TinyViT backbones. ✅
- Improves stability and reliability for half-precision inference workflows on compatible hardware. 🚀
- Delivers a low-risk bug fix with minimal code surface change, reducing regression likelihood. 🔍

## PR Review Comments

**[user]** on `ultralytics/models/sam/predict.py`:

`setup_model()` still calls `eval()` before moving the module to `device`. For TinyViT this means eval-time cached tensors (e.g. attention bias cache created in `train(False)`) are constructed on CPU and later copied to GPU during forward, which adds avoidable per-inference overhead. Consider ordering as: `model = model.to(device)` -> dtype cast (`half/float`) -> `model.eval()` -> `self.model = model`, so caches are created on the final device + dtype (and matches the device-then-dtype pattern used elsewhere, e.g. `ultralytics/nn/autobackend.py`).
```suggestion
        # Move model to device first, then cast dtype, then set eval so any eval-time caches are created on-device.
        model = model.to(device)
        model = model.half() if self.args.half else model.float()
        model.eval()
        self.model = model
```

**[user]** on `ultralytics/models/sam/predict.py`:

PR description mentions a “safety net” that aligns TinyViT cached attention-bias tensor dtype/device in the attention forward path. I don’t see such a dtype alignment change in the current code (the TinyViT cache is only moved by device, not dtype), so either the description should be updated or the additional change included to match what’s described.

**[user]** on `ultralytics/models/sam/predict.py`:

This change fixes a regression that only reproduces under FP16 inference; there’s currently CUDA SAM coverage but no assertion/coverage for `half=True` on TinyViT-based MobileSAM. Adding a small test that runs `SAM(...mobile_sam.pt).predict(..., half=True, device=cuda)` would prevent the dtype-mismatch crash from reappearing.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
