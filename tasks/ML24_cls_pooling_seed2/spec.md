# ML24: Mean Pooling vs CLS Token Pooling Mismatch

## Goal
Fix `model.py` so fine-tuning uses CLS token pooling, matching the pretrained checkpoint.
Run `python train.py` then `python check_model.py` — both must pass.

## Task
Fine-tuning a **distilled transformer with CLS pooling checkpoint** for sequence classification.
The pretrained encoder uses CLS token pooling. Fine-tuning must match.
Model must achieve >0.55 validation accuracy.

---

## The Bug: Mean Pooling on a CLS-Pooling Checkpoint

**Location**: `BertClassifier.forward()` in `model.py`

### Background: CLS Token Pooling

BERT and similar models prepend a special [CLS] token at position 0.
During pretraining (next sentence prediction, masked LM), the [CLS] token
representation is specifically optimized to aggregate sequence-level information.

For fine-tuning classification tasks, you MUST use the [CLS] representation:
```python
pooled = encoder_output[:, 0, :]  # CLS token always at position 0
```

### Current (Buggy) Code

```python
if attention_mask is not None:
    mask = attention_mask.unsqueeze(-1).float()
    pooled = (enc_out * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)  # masked mean
else:
    pooled = enc_out.mean(dim=1)  # BUG: plain mean pooling
```

**Problems**:
1. Mean pooling averages ALL token representations
2. The averaged representation was never seen during pretraining
3. Mean pooling dilutes the CLS signal with content token representations
4. The `classifier` linear layer was pretrained to take CLS features as input

### Correct Fix

```python
# Use CLS token at position 0 — matches pretraining objective
pooled = enc_out[:, 0, :]
```

This is the only change needed. The input sequences already have CLS token
prepended at position 0 (token id=1 reserved for CLS).

### Why This Matters

| Approach | Pooled rep shape | In pretraining distribution? |
|----------|------------------|------------------------------|
| CLS ✓    | (B, 64)          | Yes — always seen at pos 0   |
| Mean ✗   | (B, 64)          | No — never seen during PT    |

---

## Training Config
- embed_dim: 64, seq_len (with CLS): 15
- LR: 0.002, Epochs: 21, Batch: 16

## Deliverables
1. Fixed `model.py` using CLS token pooling
2. `training_results.json` after running `python train.py`
3. `python check_model.py` exits 0
