# ML8: Distributed Training — Amp (Automatic Mixed Precision) Training Bugs

## Goal
Fix `distributed_train.py` so training converges (loss decreases >10%).
`check_training.py` must pass all checks.

## Setup: Amp

---

## Bugs

### Bug 1: Scaler Outside Context

**Problem**: Gradscaler.scale() applied outside autocast context

**Fix**: Loss scaling must happen inside the torch.cuda.amp.autocast() context manager. Scale the loss before backward().

### Bug 2: Unscale Before Clip

**Problem**: Gradient clipping done before scaler.unscale_(optimizer)

**Fix**: Must call scaler.unscale_(optimizer) BEFORE torch.nn.utils.clip_grad_norm_(). Otherwise clipping operates on scaled gradients.

### Bug 3: Scaler Update Skipped

**Problem**: Scaler.update() not called after scaler.step()

**Fix**: Always call scaler.update() after scaler.step(optimizer). Skipping prevents the scale factor from being adjusted for the next iteration.


## Correct Amp Pattern

```python
# Correct AMP pattern
optimizer.zero_grad()
with torch.cuda.amp.autocast():  # autocast context
    out = model(xb)
    loss = criterion(out, yb)
scaler.scale(loss).backward()
scaler.unscale_(optimizer)           # unscale BEFORE clip
torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
scaler.step(optimizer)
scaler.update()                      # MUST call update()
```

## Deliverables
1. Fixed `distributed_train.py`
2. `training_results.json` with `converged: true`
3. `check_training.py` exits 0
