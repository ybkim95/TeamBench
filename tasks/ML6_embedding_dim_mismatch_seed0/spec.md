# ML6: Embedding Dimension Mismatch

## Goal
Fix `model.py` so the forward pass succeeds without dimension errors.
`check_model.py` must pass all checks.

## Architecture: Text Embedding Classifier With Projection Mismatch

### Correct Architecture Diagram

```
Input
  ↓
FeatureExtractor / EmbeddingLayer
  ├── [Layer 1: input → intermediate]
  └── [Projection: intermediate → 256]  ← MUST output 256
  ↓
Encoder / Projector
  ├── [fc1: 256 → 128]        ← MUST accept 256
  └── [fc2: 128 → 128]     ← MUST output 128
  ↓
Classifier / Head
  └── [fc: 128 → 5]       ← MUST accept 128
```

---

## Bug 1: Embedding Projection Dimension Wrong

**Location**: First module's projection/output layer

**Current (buggy)**:
```python
self.projection = nn.Linear(..., 512)  # outputs 512
```

**Correct**:
```python
self.projection = nn.Linear(..., 256)  # must output 256
```

**Error caused**: When the second module (Encoder/Projector) receives a tensor
of shape `(batch, 512)` but its `fc1 = nn.Linear(256, 128)`
expects `256` features, PyTorch raises:
```
RuntimeError: mat1 and mat2 shapes cannot be multiplied (512 != 256)
```

---

## Bug 2: Encoder Output Dimension Wrong

**Location**: Encoder/Projector's final linear layer

**Current (buggy)**:
```python
self.fc2 = nn.Linear(128, 64)  # outputs 64
```

**Correct**:
```python
self.fc2 = nn.Linear(128, 128)  # must output 128
```

**Error caused**: The Classifier/Head has `fc = nn.Linear(128, 5)`
which expects `128` features. Receiving `64` raises:
```
RuntimeError: mat1 and mat2 shapes cannot be multiplied (64 != 128)
```

---

## Dimension Flow After Fix

| Layer | Input dim | Output dim |
|-------|-----------|------------|
| EmbeddingLayer/FeatureExtractor projection | — | **256** |
| Encoder/Projector fc1 | **256** | 128 |
| Encoder/Projector fc2 | 128 | **128** |
| Classifier/Head fc | **128** | 5 |

## Deliverables
1. Fixed `model.py` with both dimension mismatches corrected
2. `model_check_results.json` with all checks True
3. `check_model.py` exits 0
