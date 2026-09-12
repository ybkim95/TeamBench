# ML13: AMP Gradient Clip Before Unscale

## Goal
Fix the AMP training loop in `train.py` so that gradient clipping works correctly
with `GradScaler`. Run `python train.py` then `python check_training.py`.

## Task
Training a **deep tabular model with AMP** using PyTorch AMP (mixed precision).

---

## The Bug: Gradient Clipping Before `scaler.unscale_()`

**Location**: `train.py`, inside the training loop

### PyTorch AMP Gradient Scaling

When using `GradScaler`, the backward pass produces **scaled gradients**:
- `scaler.scale(loss).backward()` — gradients are multiplied by `scale_factor`
  (typically initialized to 2^16 = 65536)
- Before optimizer step, `scaler.step()` internally calls `scaler.unscale_(optimizer)`
  to divide gradients back to their true values

### Current (Buggy) Code

```python
scaler.scale(loss).backward()

# BUG: clip BEFORE unscale — gradients are still scaled by 65536×
grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

# scaler.unscale_(optimizer)  # missing!
scaler.step(optimizer)
scaler.update()
```

**What happens**: `clip_grad_norm_` computes the L2 norm of scaled gradients.
With scale_factor=65536 and max_norm=1.0, the clip threshold is effectively
`1.0 / 65536 ≈ 0.000015` of the true gradient norm.
On GPU, this means gradients are **never actually clipped** — the scaled norms
are always ≫ max_norm, so all gradients get zeroed or clipped to near-zero.

### Correct Code

```python
scaler.scale(loss).backward()

scaler.unscale_(optimizer)   # MUST come first — divides gradients by scale_factor
grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)  # clip true gradients

scaler.step(optimizer)       # skip step if inf/nan detected
scaler.update()              # adjust scale_factor for next iteration
```

**Why the order matters**:
1. `scaler.unscale_(optimizer)` divides all gradients by the scale factor
2. Now gradients are in their true (unscaled) range
3. `clip_grad_norm_` clips the true L2 norm to `max_norm=1.0`
4. `scaler.step()` checks for inf/nan and applies the update

### Note on the Test Setup
The workspace uses `GradScaler(enabled=False)` (CPU mode) so training runs without
errors. However, the code structure with the wrong order is what matters — on a GPU
with `enabled=True`, the bug would cause gradients to never be clipped.
The fix must call `scaler.unscale_(optimizer)` before `clip_grad_norm_`.

---

## Deliverables
1. Fixed `train.py` with correct `unscale_` → `clip_grad_norm_` order
2. `training_results.json` after running `python train.py`
3. `python check_training.py` exits 0
