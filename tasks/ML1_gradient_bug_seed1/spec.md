# ML1: Gradient Bug — Selective Fix

## Situation

Static analysis of `train.py` and `model.py` has flagged **6 issues**.
`TRAINING_DESIGN.md` documents 3 of them as #  choices.
This spec documents the remaining **3 genuine bugs** that must be fixed.

**Critical**: Fixing the #  choices will cause the model to
diverge or underperform. Read `TRAINING_DESIGN.md` and this spec together.

---

## Real Bug 1: Wrong Loss Function

**Task type**: Multiclass Classification

**Current (buggy)**:
```python
criterion = nn.BCEWithLogitsLoss()
```

**Correct**:
```python
criterion = nn.CrossEntropyLoss()
```

**Reason**: BCEWithLogitsLoss expects binary (0/1) targets per class and applies independent sigmoid activations. Multiclass classification with mutually exclusive classes requires CrossEntropyLoss, which applies softmax and computes the negative log-likelihood of the correct class.

---

## Real Bug 2: Learning Rate Too High

**Current (buggy)**:
```python
optimizer = optim.AdamW(model.parameters(), lr=5.0, weight_decay=...)
```

**Correct**: Change `lr=5.0` to `lr=0.001`. Leave all other
`AdamW` arguments unchanged — in particular `weight_decay=0.1` is **intentional**
(see TRAINING_DESIGN.md §Weight Decay).

**Reason**: lr=5.0 is catastrophically large for Adam on a classification task. Gradient updates of this magnitude cause immediate weight explosion. Standard Adam learning rates are 1e-3 to 1e-4.

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
- Input dim: `20`
- Hidden layers: `[128, 64, 32]`
- Output dim: `5`
- Dropout: `0.2`
- Training epochs: 24, batch size: 32

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

**Why it is intentional**: gain=2.0 for xavier_uniform_ is intentional for this Fixup-style architecture. The extra gain compensates for variance reduction through the BatchNorm-ReLU chain so that the signal magnitude is preserved at initialisation. The standard gain=1.0 would cause gradient vanishing.

**Do not change** `gain=2.0` to `gain=1.0` or remove `_init_weights()`.

---

## §Weight Decay — `AdamW(weight_decay=0.1)`

**What analysis flags**: `weight_decay=0.1` is much higher than typical values
(0.01 or lower). Some style guides warn about high weight decay with Adam-family
optimisers.

**Why it is intentional**: AdamW weight_decay=0.1 is the prescribed regularisation strength for this architecture class. It prevents memorisation of the training set without interfering with the adaptive gradient scaling.

**Do not reduce** `weight_decay` below 0.05 or switch to `optim.Adam` (which
does not correctly decouple weight decay from the adaptive update).

---

## §Schedule — `CosineAnnealingWarmRestarts`

**What analysis flags**: The learning-rate schedule causes LR to *increase*
periodically. Analysis tools may flag this as "unstable training" or "LR
oscillation".

**Why it is intentional**: Cosine annealing with warm restarts is intentional. The periodic LR increases are not bugs — they allow the optimiser to escape sharp minima discovered in previous cycles. The loss temporarily increases at each restart; this is expected and correct.

**Do not replace** `CosineAnnealingWarmRestarts` with `StepLR`, `ReduceLROnPlateau`,
or a plain cosine decay without restarts.

---

## Known Real Bugs (NOT documented here)

There are bugs in `train.py` that *are* genuine and must be fixed.
Consult the spec for details. The three sections above describe only the
**intentional** choices that must be preserved.
