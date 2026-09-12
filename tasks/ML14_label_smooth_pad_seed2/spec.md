# ML14: Label Smoothing Leaks to PAD Token

## Goal
Fix `smooth_loss.py` so label smoothing correctly excludes the PAD token.
Run `python train.py` then `python check_training.py`.

## Task
Training a **token classification / translation model** with label smoothing (epsilon=0.15).
Vocabulary size: 60, PAD token index: 0.

---

## The Bug: Label Smoothing Includes PAD Token

**Location**: `smooth_loss.py`, `LabelSmoothingLoss.forward()`

### Background: Label Smoothing

Label smoothing replaces hard one-hot targets with soft distributions:
- True token gets probability: `1 - epsilon = 0.85`
- Other tokens share: `epsilon = 0.15` distributed uniformly

This prevents overconfidence and improves generalization.

### Bug 1: PAD Token Receives Smoothing Mass

**Current (buggy)**:
```python
smooth_dist = torch.full(
    (B, self.vocab_size),
    self.epsilon / (self.vocab_size - 1),  # includes PAD
    device=logits.device
)
smooth_dist.scatter_(1, targets.unsqueeze(1), 1.0 - self.epsilon)
# PAD column still has epsilon/(vocab_size-1) mass
```

**Correct**:
```python
smooth_dist = torch.zeros(B, self.vocab_size, device=logits.device)
# Distribute smoothing mass only to non-PAD tokens
n_real = self.vocab_size - 1  # exclude PAD
smooth_dist.fill_(self.epsilon / (n_real - 1))  # all non-true tokens
smooth_dist[:, self.pad_idx] = 0.0              # zero out PAD
smooth_dist.scatter_(1, targets.unsqueeze(1), 1.0 - self.epsilon)
```

**Why it matters**: The model is trained to assign `0.00254` probability
to PAD as an output token. This corrupts the output distribution and causes the
model to occasionally predict PAD for real positions.

### Bug 2: PAD Target Positions Not Masked

**Current (buggy)**:
```python
loss = -(smooth_dist * log_probs).sum(dim=-1)  # includes PAD target positions
return loss.mean()
```

**Correct**:
```python
loss = -(smooth_dist * log_probs).sum(dim=-1)  # (B,)
# Mask out positions where target is PAD
pad_mask = (targets != self.pad_idx).float()
return (loss * pad_mask).sum() / pad_mask.sum().clamp(min=1)
```

**Why it matters**: Positions where `target == PAD_IDX` are padding — the model
should not be penalized for what it predicts there. Including them in the loss
dilutes the learning signal from real tokens.

---

## Deliverables
1. Fixed `smooth_loss.py` with both bugs corrected
2. `training_results.json` after running `python train.py`
3. `python check_training.py` exits 0
