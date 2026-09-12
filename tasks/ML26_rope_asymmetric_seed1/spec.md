# ML26: RoPE Applied Asymmetrically (K Only, Not Q)

## Goal
Fix `rope_attention.py` so RoPE is applied to BOTH queries and keys.
Run `python train.py` then `python check_rope.py` — both must pass.

## Task
Training a **RoPE-based sequence classifier** for sequence classification.
Model must achieve >0.55 validation accuracy.

---

## The Bug: RoPE Applied to Keys But Not Queries

**Location**: `RoPEAttention.forward()` in `rope_attention.py`

### Background: Rotary Position Embedding (RoPE)

RoPE (Su et al., 2021) encodes position by rotating the query/key vectors:
```
q_rot[m] = R_m · q   (rotation matrix for position m)
k_rot[n] = R_n · k   (rotation matrix for position n)
```

The key property: `q_rot[m] · k_rot[n] = q · (R_{n-m} · k)`

This means the attention score depends only on the **relative position** `n - m`,
not absolute positions. This property requires BOTH Q and K to be rotated.

### Current (Buggy) Code

```python
cos = self.rope_cos[:T].unsqueeze(0).unsqueeze(0)
sin = self.rope_sin[:T].unsqueeze(0).unsqueeze(0)

# BUG: only K is rotated
k = apply_rope(k, cos, sin)
# q = apply_rope(q, cos, sin)  # MISSING — q has no positional info

attn = F.softmax((q @ k.transpose(-2, -1)) * self.scale, dim=-1)
```

**Without rotating Q**:
- Attention score: `q · (R_n · k)` — depends on absolute position of K
- No relative position information from Q's perspective
- Each query sees all keys with the same positional sensitivity
- The relative position invariance property is broken

### Correct Fix

```python
cos = self.rope_cos[:T].unsqueeze(0).unsqueeze(0)
sin = self.rope_sin[:T].unsqueeze(0).unsqueeze(0)

# Apply RoPE to BOTH Q and K
q = apply_rope(q, cos, sin)  # ADD THIS LINE
k = apply_rope(k, cos, sin)
```

After the fix: attention score `q_rot[m] · k_rot[n]` = `q · R_{n-m} · k`
which depends only on the offset `n - m` (relative position).

### RoPE Implementation Details

```python
def apply_rope(x, cos, sin):
    # x: (B, H, T, head_dim)
    return x * cos + rotate_half(x) * sin

def rotate_half(x):
    half = x.shape[-1] // 2
    return torch.cat([-x[..., half:], x[..., :half]], dim=-1)
```

---

## Training Config
- embed_dim: 48, num_heads: 4, head_dim: 12
- seq_len: 20, LR: 0.002, Epochs: 29, Batch: 16

## Deliverables
1. Fixed `rope_attention.py` with `q = apply_rope(q, cos, sin)` added
2. `training_results.json` after running `python train.py`
3. `python check_rope.py` exits 0
