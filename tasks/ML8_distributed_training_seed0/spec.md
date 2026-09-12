# ML8: Distributed Training — Gradient Accumulation Over Micro-Batches

## Goal
Fix `distributed_train.py` so training converges (loss decreases >10%).
`check_training.py` must pass all checks.

## Setup: Gradient Accumulation

---

## Bugs

### Bug 1: Zero Grad Inside Loop

**Problem**: Optimizer.zero_grad() called inside accumulation loop (clears accumulated gradients)

**Fix**: Move optimizer.zero_grad() to BEFORE the accumulation loop, not inside it.

### Bug 2: Missing Loss Scaling

**Problem**: Loss not divided by accumulation_steps (gradients too large)

**Fix**: Divide loss by accumulation_steps before backward: loss = loss / accumulation_steps

### Bug 3: Step Every Iteration

**Problem**: Optimizer.step() called every micro-batch instead of after full accumulation

**Fix**: Only call optimizer.step() after processing all accumulation_steps micro-batches.


## Correct Gradient Accumulation Pattern

```python
# Correct gradient accumulation
optimizer.zero_grad()  # BEFORE the accumulation loop
for step in range(ACCUMULATION_STEPS):
    xb, yb = get_micro_batch(step)
    out = model(xb)
    loss = criterion(out, yb) / ACCUMULATION_STEPS  # Scale by accum steps
    loss.backward()  # Gradients accumulate
# AFTER all micro-batches:
optimizer.step()  # Only once per effective batch
```

## Deliverables
1. Fixed `distributed_train.py`
2. `training_results.json` with `converged: true`
3. `check_training.py` exits 0
