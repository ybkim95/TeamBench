# ML22: LayerNorm Placement Broken Hybrid

## Goal
Fix `transformer.py` so LayerNorm uses a consistent placement strategy.
Run `python train.py` then `python check_transformer.py` — both must pass.

## Task
Training a **small transformer classifier** for sequence classification.
Model must achieve >0.55 validation accuracy.

---

## The Bug: Inconsistent Pre-norm/Post-norm Mix

**Location**: `TransformerBlock.forward()` in `transformer.py`

### Background: Pre-norm vs Post-norm

**Post-norm** (original Transformer, Wang et al.):
```python
x = LayerNorm(x + Attention(x))  # norm after residual
x = LayerNorm(x + FFN(x))        # norm after residual
```

**Pre-norm** (GPT, most modern transformers):
```python
x = x + Attention(LayerNorm(x))  # norm before sublayer
x = x + FFN(LayerNorm(x))        # norm before sublayer
```

Pre-norm is generally preferred: more stable gradients, no warmup needed.

### Current (Buggy) Code

```python
def forward(self, x):
    # POST-norm for attention:
    x = self.norm1(x + self.attn(x))   # norm(residual + sublayer(input))
    # PRE-norm for FFN (but wrong):
    x = x + self.ff(self.norm2(x))     # x + sublayer(norm(x))
```

**Problems with this mix**:
1. After attention: `x` is normalized (output of norm1)
2. FFN then gets `norm2(normalized_x)` — double normalization on this path
3. Gradients flow differently through the two sublayers
4. With 2 layers, these inconsistencies compound

### Correct Pre-norm Fix

```python
def forward(self, x):
    x = x + self.attn(self.norm1(x))  # pre-norm: norm before attn
    x = x + self.ff(self.norm2(x))    # pre-norm: norm before ff
```

Or correct post-norm:
```python
def forward(self, x):
    x = self.norm1(x + self.attn(x))  # post-norm: norm after attn residual
    x = self.norm2(x + self.ff(x))    # post-norm: norm after ff residual
```

**Choose pre-norm** (more stable for training from scratch).

---

## Training Config
- embed_dim: 32, num_layers: 2
- LR: 0.002, Epochs: 26, Batch: 16

## Deliverables
1. Fixed `transformer.py` with consistent norm placement
2. `training_results.json` after running `python train.py`
3. `python check_transformer.py` exits 0
