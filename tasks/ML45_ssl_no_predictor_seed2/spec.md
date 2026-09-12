# ML45: SSL Collapse Without Predictor MLP (BYOL)

## Goal
Fix `byol.py` so the BYOL online network applies the predictor MLP.
Run `python train.py` then `python check_byol.py` — both must pass.

## Task
Training **tabular data self-supervised learning** with BYOL-style self-supervised learning.
The model must achieve >0.55 linear probe accuracy on downstream classification.

---

## The Bug: Missing Predictor MLP

**Location**: `byol.py` `BYOL.loss()` — predictor not applied to online projections

### Background: Why BYOL Needs a Predictor

BYOL (Grill et al. 2020) has two networks:
- **Online** network: updated by gradients, has predictor MLP on top
- **Target** network: slow EMA copy of online, NO predictor

The key asymmetry: only the online network has the predictor.

Without the predictor:
- Online and target have identical architectures
- The trivial solution is both collapse to the same constant
- No gradient signal prevents this collapse

With the predictor:
- Online must predict target projections through the predictor bottleneck
- This asymmetry breaks the trivial solution
- The EMA + predictor combination prevents collapse without negative pairs

### Current (Buggy) Code

```python
def loss(self, x1, x2):
    _, online_z1 = self.online(x1)
    _, online_z2 = self.online(x2)
    # BUG: predictor not applied
    pred_z1 = online_z1   # should be self.predictor(online_z1)
    pred_z2 = online_z2   # should be self.predictor(online_z2)
    ...
```

### Correct Fix

```python
def loss(self, x1, x2):
    _, online_z1 = self.online(x1)
    _, online_z2 = self.online(x2)
    # FIXED: apply predictor to online projections
    pred_z1 = self.predictor(online_z1)
    pred_z2 = self.predictor(online_z2)
    ...
```

---

## Training Config
- EMA decay: 0.99, lr: 0.001, Epochs: 32, Batch: 32

## Deliverables
1. Fixed `byol.py` with predictor applied in `loss()`
2. `training_results.json` after running `python train.py`
3. `python check_byol.py` exits 0
