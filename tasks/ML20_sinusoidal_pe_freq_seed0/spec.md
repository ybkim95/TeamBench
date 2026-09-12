# ML20: Sinusoidal PE Frequency Step Bug

## Goal
Fix `positional_encoding.py` so sinusoidal PE uses the correct frequency bands.
Run `python train.py` then `python check_pe.py` — both must pass.

## Task
Training a **transformer encoder with sinusoidal PE** that requires correct positional information.
Model must achieve >0.55 validation accuracy on position-sensitive classification.

---

## The Bug: `arange` step=1 Instead of step=2

**Location**: `SinusoidalPE.__init__()` in `positional_encoding.py`

### Background: Sinusoidal Positional Encoding

From Vaswani et al. (2017), the correct formula is:
```
PE(pos, 2i)   = sin(pos / 10000^(2i / d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i / d_model))
```

Where `i` ranges over `0, 1, ..., d_model//2 - 1`.
Key property: dimensions `2i` and `2i+1` share the **same frequency** — they are
a sin/cos pair at that frequency.

### Current (Buggy) Code

```python
div_term = torch.exp(
    torch.arange(0, embed_dim, step=1).float()  # BUG: step=1
    * (-math.log(10000.0) / embed_dim)
)
pe[:, 0::2] = torch.sin(position * div_term[:embed_dim // 2 + embed_dim % 2])
pe[:, 1::2] = torch.cos(position * div_term[:embed_dim // 2])
```

With `step=1`: `div_term` = `[f(0), f(1), f(2), ..., f(d-1)]`
- `pe[:, 0]` uses `f(0)`, `pe[:, 2]` uses `f(1)`, `pe[:, 4]` uses `f(2)` ...
- `pe[:, 1]` uses `f(0)`, `pe[:, 3]` uses `f(1)` ...

The sin and cos at dimension 0 and 1 use `f(0)` — accidentally correct!
But `pe[:, 2]` (sin) uses `f(1)` and `pe[:, 3]` (cos) uses `f(1)` — the
indexing into div_term is off, causing incorrect frequency assignments.

### Correct Fix

```python
div_term = torch.exp(
    torch.arange(0, embed_dim, step=2).float()  # step=2: [0, 2, 4, ..., d-2]
    * (-math.log(10000.0) / embed_dim)
)
pe[:, 0::2] = torch.sin(position * div_term)
pe[:, 1::2] = torch.cos(position * div_term)
```

With `step=2`: `div_term` has `d_model//2` elements.
- `pe[:, 0]` = sin(pos * f(0)), `pe[:, 1]` = cos(pos * f(0)) — same frequency
- `pe[:, 2]` = sin(pos * f(2)), `pe[:, 3]` = cos(pos * f(2)) — same frequency
- The property `sin^2 + cos^2 = 1` holds for each pair

---

## Training Config
- Embedding dim: 32, Max length: 128
- Learning rate: 0.002, Epochs: 26, Batch size: 16

## Deliverables
1. Fixed `positional_encoding.py` with `step=2` in arange
2. `training_results.json` after running `python train.py`
3. `python check_pe.py` exits 0
