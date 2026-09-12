# ML21: Multi-Head Attention Splits Wrong Dimension

## Goal
Fix `attention.py` so multi-head attention splits the embedding dimension correctly.
Run `python train.py` then `python check_attention.py` — both must pass.

## Task
Training a **multi-head attention encoder** for sequence classification.
Model must achieve >0.55 validation accuracy.

---

## The Bug: Reshaping Splits Sequence Dim Instead of Embed Dim

**Location**: `MultiHeadAttention.forward()` in `attention.py`

### Background: Correct MHA Reshape

Multi-head attention splits the embedding dimension across heads:
```
Input Q: (B, T, embed_dim)  where embed_dim = num_heads * head_dim
Correct reshape: (B, T, num_heads, head_dim).transpose(1, 2) -> (B, num_heads, T, head_dim)
Each head attends over ALL T positions with head_dim features.
```

### Current (Buggy) Code

```python
q = q.reshape(B, self.num_heads, T // self.num_heads, C)  # BUG
k = k.reshape(B, self.num_heads, T // self.num_heads, C)  # BUG
v = v.reshape(B, self.num_heads, T // self.num_heads, C)  # BUG
```

This splits `T` into `(num_heads, T//num_heads)` — each head sees a
**slice of time** with full embedding dimension `C`. Consequences:
1. Each head can only attend to `T//num_heads = 16//4 = 4` positions
2. Attention scores are `(T//H, C) @ (C, T//H)` which are C×C products — wrong scale
3. Heads don't learn diverse representations (they see different time slices, not different features)

### Correct Fix

```python
q = q.reshape(B, T, self.num_heads, self.head_dim).transpose(1, 2)  # (B, num_heads, T, head_dim)
k = k.reshape(B, T, self.num_heads, self.head_dim).transpose(1, 2)
v = v.reshape(B, T, self.num_heads, self.head_dim).transpose(1, 2)
attn = (q @ k.transpose(-2, -1)) * self.scale  # self.scale = head_dim^-0.5
...
out = attn @ v  # (B, num_heads, T, head_dim)
out = out.transpose(1, 2).reshape(B, T, C)  # merge heads back
```

Key changes:
- `head_dim = embed_dim // num_heads = 32 // 4 = 8`
- Attention scale is `head_dim^-0.5 = 8^-0.5`, not `C^-0.5`
- After `attn @ v`, transpose back before reshape

---

## Training Config
- embed_dim: 32, num_heads: 4, head_dim: 8
- Sequence length: 16, LR: 0.002, Epochs: 26, Batch: 16

## Deliverables
1. Fixed `attention.py` with correct embed_dim split
2. `training_results.json` after running `python train.py`
3. `python check_attention.py` exits 0
