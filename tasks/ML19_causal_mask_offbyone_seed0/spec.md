# ML19: Causal Mask Off-by-One Lookahead Leak

## Goal
Fix `model.py` so the causal attention mask is correct.
Run `python train.py` then `python check_model.py` — both must pass.

## Task
Training a **tiny GPT-style causal language model** for next-token prediction.
Model must achieve >0.55 validation accuracy on sequence patterns.

---

## The Bug: Wrong `diagonal` Parameter in Causal Mask

**Location**: `CausalSelfAttention.__init__()` in `model.py`

### Current (Buggy) Code

```python
# BUG: diagonal=0 masks the diagonal — token cannot attend to itself
mask = torch.triu(torch.ones(seq_len, seq_len), diagonal=0).bool()
```

**What `torch.triu` does**:
- `diagonal=0`: zeroes (or keeps) elements at and above the main diagonal
- `diagonal=1`: zeroes (or keeps) elements strictly above the main diagonal

When `mask[i, j] = True` means "block attention from position i to position j":
- With `diagonal=0`: position `i` cannot attend to position `i` itself (diagonal is blocked)
- With `diagonal=1` (correct): position `i` can attend to `i` and all positions `j < i`

### Correct Fix

```python
# Correct: diagonal=1 — only mask strictly future positions
mask = torch.triu(torch.ones(seq_len, seq_len), diagonal=1).bool()
```

**Why this matters**:
- Each token needs to attend to itself to incorporate its own representation
- With `diagonal=0`, the softmax over masked positions produces uniform attention
  over past tokens only, losing the token's own embedding signal
- This breaks the residual stream information flow through attention

### Causal Mask Shape (seq_len=16)

| diagonal | [0,0] | [0,1] | [1,0] | [1,1] | Meaning |
|----------|-------|-------|-------|-------|---------|
| =0 (bug) | True  | True  | False | True  | self-masked |
| =1 (fix) | False | True  | False | False | correct causal |

---

## Training Config
- Embedding dim: 32, Sequence length: 16
- Learning rate: 0.002, Epochs: 21, Batch size: 16

## Deliverables
1. Fixed `model.py` with `diagonal=1` in causal mask
2. `training_results.json` after running `python train.py`
3. `python check_model.py` exits 0
