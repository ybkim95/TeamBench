# ML8: Distributed Training — Distributeddataparallel Gradient Synchronization Bugs

## Goal
Fix `distributed_train.py` so training converges (loss decreases >10%).
`check_training.py` must pass all checks.

## Setup: Ddp Simulation

---

## Bugs

### Bug 1: Allreduce Before Backward

**Problem**: Manual all-reduce called before loss.backward() (operates on zero/stale gradients)

**Fix**: Never manually all-reduce before backward(). DDP auto-syncs during backward(). If manual all-reduce is needed, do it after backward() on .grad tensors.

### Bug 2: No Sync Context Misuse

**Problem**: Model.no_sync() context used incorrectly — wraps the update step instead of non-final accumulation steps

**Fix**: model.no_sync() should wrap all micro-batches EXCEPT the last one in gradient accumulation. Never use no_sync() around the optimizer.step().

### Bug 3: Barrier Missing

**Problem**: Dist.barrier() missing after model save (workers can diverge)

**Fix**: After rank-0 saves checkpoint, call dist.barrier() so all workers wait before proceeding.


## Correct Ddp Simulation Pattern

```python
# Correct DDP gradient sync
optimizer.zero_grad()
out = model(xb)
loss = criterion(out, yb)
loss.backward()  # DDP all-reduces here automatically
# Manual all-reduce (if needed) goes AFTER backward:
simulate_allreduce(list(model.parameters()))
optimizer.step()
```

## Deliverables
1. Fixed `distributed_train.py`
2. `training_results.json` with `converged: true`
3. `check_training.py` exits 0
