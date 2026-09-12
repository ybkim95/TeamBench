# ML11: LR Warmup-Decay Composition Order Bug

## Goal
Fix `scheduler.py` so that the warmup-cosine learning rate schedule works correctly.
Run `python train.py` then `python check_training.py` — both must pass.

## Task
Training a **small transformer language model** for sequence_classification.
Model must achieve >0.65 validation accuracy.

---

## The Bug: Wrong Composition Order in `scheduler.py`

**Location**: `WarmupCosineScheduler.get_lr()` in `scheduler.py`

### Current (Buggy) Logic

```python
def get_lr(self) -> float:
    step = self._step
    # Cosine decay computed over ALL steps first
    cosine_lr = 0.5 * self.base_lr * (
        1 + math.cos(math.pi * step / max(self.total_steps, 1))
    )
    if step < self.warmup_steps:
        # Warmup applied on top of already-decayed value — WRONG
        return cosine_lr * (step / max(self.warmup_steps, 1))
    return cosine_lr
```

**What goes wrong**:
1. `cosine_lr` at step 1 is already decayed slightly below `base_lr`
2. During warmup, we scale this already-decayed value — the LR starts near 0 but
   ramps to ~`cosine_lr(warmup_steps)`, which is LESS than `base_lr`
3. After warmup ends (step = `warmup_steps`), the scheduler jumps to wherever
   `cosine_lr` is at that step — creating a discontinuity
4. The effective peak LR is lower than intended, and the cosine decay
   continues from wherever `cosine_lr` is rather than from `base_lr`

### Correct Logic

```python
def get_lr(self) -> float:
    step = self._step
    if step < self.warmup_steps:
        # Linear warmup: ramp from 0 to base_lr
        return self.base_lr * (step / max(self.warmup_steps, 1))
    # Cosine decay over remaining steps AFTER warmup
    progress = (step - self.warmup_steps) / max(self.total_steps - self.warmup_steps, 1)
    return 0.5 * self.base_lr * (1 + math.cos(math.pi * progress))
```

**Why this is correct**:
1. During warmup (0 → warmup_steps): LR linearly ramps from 0 to `base_lr`
2. After warmup: cosine decay progresses from `base_lr` down to ~0 over
   the remaining `total_steps - warmup_steps` steps
3. The two phases connect continuously at step `warmup_steps` where both
   formulas yield `base_lr`

---

## Training Config
- Base LR: `0.002`
- Warmup ratio: `0.2` of total steps
- Epochs: 26, Batch size: 32
- Optimizer: AdamW with weight_decay=1e-4

## Deliverables
1. Fixed `scheduler.py`
2. `training_results.json` after running `python train.py`
3. `python check_training.py` exits 0
