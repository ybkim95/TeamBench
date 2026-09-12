# ML1: Gradient Bug — Selective Fix

## Situation

Static analysis of `train.py` and `model.py` has flagged **6 issues**.
`TRAINING_DESIGN.md` documents 3 of them as #  choices.
This spec documents the remaining **3 genuine bugs** that must be fixed.

**Critical**: Fixing the #  choices will cause the model to
diverge or underperform. Read `TRAINING_DESIGN.md` and this spec together.

---

## Real Bug 1: Wrong Loss Function

**Task type**: Binary Classification

**Current (buggy)**:
```python
criterion = nn.MSELoss()
```

**Correct**:
```python
criterion = nn.BCEWithLogitsLoss()
```

**Reason**: MSELoss is designed for regression with continuous targets. Binary classification with logit outputs requires BCEWithLogitsLoss, which fuses the sigmoid activation with the cross-entropy loss for numerical stability. MSELoss on logits produces gradient magnitudes that do not reflect classification confidence, causing slow convergence.

---

## Real Bug 2: Learning Rate Too High

**Current (buggy)**:
```python
optimizer = optim.AdamW(model.parameters(), lr=1.0, weight_decay=...)
```

**Correct**: Change `lr=1.0` to `lr=0.001`. Leave all other
`AdamW` arguments unchanged — in particular `weight_decay=0.1` is **intentional**
(see TRAINING_DESIGN.md §Weight Decay).

**Reason**: Adam with lr=1.0 produces weight updates orders of magnitude larger than the gradient signal. Weights diverge to ±∞ within a few batches, producing NaN losses. Standard practice for Adam with BCEWithLogitsLoss is 1e-3.

---

## Real Bug 3: BatchNorm in Wrong Mode During Evaluation

**Location**: `evaluate()` function in `train.py`

**Current (buggy)**:
```python
def evaluate(model, X_val, y_val):
    model.train()  # BUG: uses noisy batch statistics
    ...
```

**Correct**:
```python
def evaluate(model, X_val, y_val):
    model.eval()   # Uses accumulated running statistics
    ...
```

**Reason**: `nn.BatchNorm1d` in `train` mode normalises using the current mini-batch
statistics. On a validation batch these statistics are noisy and produce incorrect
normalisation, making val_metric unreliable. `eval` mode uses the running mean/variance
accumulated during training.

After calling `model.eval()` the function should call `model.train()` at the end
(or use a context manager) — but the training loop already calls `model.train()`
at the top of each epoch, so no additional restore is needed.

---

## Intentional Choices (DO NOT CHANGE)

These are **not bugs**. Changing them will break training:

| Choice | Location | Why Intentional |
|--------|----------|-----------------|
| `xavier_uniform_(gain=2.0)` | `model.py::_init_weights` | Fixup-style initialisation for BatchNorm networks |
| `weight_decay=0.1` | `train.py::AdamW(...)` | Strong regularisation per architecture recipe |
| `CosineAnnealingWarmRestarts` | `train.py` | Prescribed LR schedule; restarts are correct |

See `TRAINING_DESIGN.md` for full rationale.

---

## Architecture
- Input dim: `16`
- Hidden layers: `[64, 32]`
- Output dim: `1`
- Dropout: `0.3`
- Training epochs: 21, batch size: 32

## Deliverables
1. Fixed `train.py` with the 3 real bugs corrected, intentional choices untouched
2. `training_results.json` present after `python train.py`
3. `check_training.py` exits 0 (all checks pass, including preservation checks)


# Training Design Document

This document explains deliberate design decisions in `train.py` and `model.py`
that a static analyser or naive code review may flag as problems.

**Read this before modifying any training code.**

---

## §Initialisation — `model._init_weights()` with `gain=2.0`

**What analysis flags**: `xavier_uniform_` called with non-standard `gain=2.0`
(default is 1.0). Linters may warn "unusual gain value".

**Why it is intentional**: This architecture uses Fixup-style initialisation (Zhang et al., 2019). The gain=2.0 passed to xavier_uniform_ is intentional: it counteracts the variance collapse introduced by the BatchNorm layers when the network is initialised. Using the default gain=1.0 causes the first few epochs to have near-zero gradients through BatchNorm.

**Do not change** `gain=2.0` to `gain=1.0` or remove `_init_weights()`.

---

## §Weight Decay — `AdamW(weight_decay=0.1)`

**What analysis flags**: `weight_decay=0.1` is much higher than typical values
(0.01 or lower). Some style guides warn about high weight decay with Adam-family
optimisers.

**Why it is intentional**: Weight decay of 0.1 is intentional per the training recipe for this architecture. With AdamW (as opposed to Adam+L2), high weight decay acts as a strong implicit regulariser without affecting the adaptive learning rate schedule. Reducing it causes the model to overfit.

**Do not reduce** `weight_decay` below 0.05 or switch to `optim.Adam` (which
does not correctly decouple weight decay from the adaptive update).

---

## §Schedule — `CosineAnnealingWarmRestarts`

**What analysis flags**: The learning-rate schedule causes LR to *increase*
periodically. Analysis tools may flag this as "unstable training" or "LR
oscillation".

**Why it is intentional**: The cosine annealing schedule with warm restarts (SGDR, Loshchilov & Hutter 2017) is the intended LR schedule for this architecture. The apparent 'oscillation' in the loss curve is correct behaviour — each restart allows the model to escape sharp local minima. Replacing it with a monotone schedule degrades final accuracy.

**Do not replace** `CosineAnnealingWarmRestarts` with `StepLR`, `ReduceLROnPlateau`,
or a plain cosine decay without restarts.

---

## Known Real Bugs (NOT documented here)

There are bugs in `train.py` that *are* genuine and must be fixed.
Consult the spec for details. The three sections above describe only the
**intentional** choices that must be preserved.
