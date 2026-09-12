# ML6: Embedding Dimension Mismatch

## Goal
Fix `model.py` so the forward pass succeeds without dimension errors.
`check_model.py` must pass all checks.

## Architecture: Cnn Feature Extractor With Fc Layer Mismatch

### Correct Architecture Diagram

```
Input
  ↓
FeatureExtractor / EmbeddingLayer
  ├── [Layer 1: input → intermediate]
  └── [Projection: intermediate → 512]  ← MUST output 512
  ↓
Encoder / Projector
  ├── [fc1: 512 → 256]        ← MUST accept 512
  └── [fc2: 256 → 256]     ← MUST output 256
  ↓
Classifier / Head
  └── [fc: 256 → 10]       ← MUST accept 256
```

---

## Bug 1: Embedding Projection Dimension Wrong

**Location**: First module's projection/output layer

**Current (buggy)**:
```python
self.projection = nn.Linear(..., 256)  # outputs 256
```

**Correct**:
```python
self.projection = nn.Linear(..., 512)  # must output 512
```

**Error caused**: When the second module (Encoder/Projector) receives a tensor
of shape `(batch, 256)` but its `fc1 = nn.Linear(512, 256)`
expects `512` features, PyTorch raises:
```
RuntimeError: mat1 and mat2 shapes cannot be multiplied (256 != 512)
```

---

## Bug 2: Encoder Output Dimension Wrong

**Location**: Encoder/Projector's final linear layer

**Current (buggy)**:
```python
self.fc2 = nn.Linear(256, 128)  # outputs 128
```

**Correct**:
```python
self.fc2 = nn.Linear(256, 256)  # must output 256
```

**Error caused**: The Classifier/Head has `fc = nn.Linear(256, 10)`
which expects `256` features. Receiving `128` raises:
```
RuntimeError: mat1 and mat2 shapes cannot be multiplied (128 != 256)
```

---

## Dimension Flow After Fix

| Layer | Input dim | Output dim |
|-------|-----------|------------|
| EmbeddingLayer/FeatureExtractor projection | — | **512** |
| Encoder/Projector fc1 | **512** | 256 |
| Encoder/Projector fc2 | 256 | **256** |
| Classifier/Head fc | **256** | 10 |

## Deliverables
1. Fixed `model.py` with both dimension mismatches corrected
2. `model_check_results.json` with all checks True
3. `check_model.py` exits 0
