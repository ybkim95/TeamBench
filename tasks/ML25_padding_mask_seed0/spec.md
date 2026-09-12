# ML25: Causal Mask Without Padding Mask

## Goal
Fix `model.py` so attention applies BOTH causal mask AND padding mask.
Run `python train.py` then `python check_model.py` — both must pass.

## Task
Training a **causal language model with variable-length sequences** on sequences with variable lengths (padded to 24).
Model must achieve >0.50 validation accuracy on next-token prediction.

---

## The Bug: Missing Padding Mask in Causal Attention

**Location**: `CausalAttention.forward()` in `model.py`

### Background: Two Masks Required

For variable-length padded batches, causal attention needs two masks:

1. **Causal mask** (upper triangular): prevent attending to future positions
2. **Padding mask**: prevent attending to PAD token positions

Without the padding mask, PAD tokens:
- Can be attended to by real tokens (attention weight to PAD ≠ 0)
- Produce attention outputs that flow back through gradients
- Pollute the representation of real tokens near sequence ends

### Current (Buggy) Code

```python
def forward(self, x, padding_mask=None):
    ...
    attn = (q @ k.transpose(-2, -1)) * self.scale

    # Only causal mask applied
    causal = self.causal_mask[:T, :T]
    attn = attn.masked_fill(causal.unsqueeze(0).unsqueeze(0), float("-inf"))

    # BUG: padding_mask never applied — PAD keys not blocked
    attn = F.softmax(attn, dim=-1)
```

### Correct Fix

```python
def forward(self, x, padding_mask=None):
    ...
    attn = (q @ k.transpose(-2, -1)) * self.scale

    # Apply causal mask
    causal = self.causal_mask[:T, :T]
    attn = attn.masked_fill(causal.unsqueeze(0).unsqueeze(0), float("-inf"))

    # Apply padding mask — mask key positions that are PAD
    if padding_mask is not None:
        # padding_mask: (B, T) True = PAD
        # Expand to (B, 1, 1, T) to broadcast over heads and query positions
        pad = padding_mask.unsqueeze(1).unsqueeze(2)
        attn = attn.masked_fill(pad, float("-inf"))

    attn = F.softmax(attn, dim=-1)
    attn = torch.nan_to_num(attn, nan=0.0)  # handle rows that are all -inf
```

**Note**: The padding mask blocks KEY positions (columns in attention matrix),
preventing all queries from attending to PAD tokens.

---

## Training Config
- embed_dim: 32, max_seq_len: 24
- ~30% of each sequence is padding on average
- LR: 0.002, Epochs: 21, Batch: 16

## Deliverables
1. Fixed `model.py` with padding mask applied
2. `training_results.json` after running `python train.py`
3. `python check_model.py` exits 0
