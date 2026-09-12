# ML12: Residual Init Variance Accumulation

## Goal
Fix the residual block initialization in `model.py` so that deep ResNet training
converges properly. Run `python train.py` then `python check_training.py`.

## Task
Training a **residual network for regression** with **10 residual blocks**.
Each block computes: `output = activation(x + F(x))`

---

## The Bug: Xavier Init in Deep Residual Blocks

**Location**: `model.py`, `ResBlock.__init__()` — the `fc2` layer

### Why This Fails

In a residual network with N=10 blocks, the output of block i is:
```
h_i = activation(h_(i-1) + F(h_(i-1)))
```

If `F` is initialized with Xavier uniform (default), each block's branch `F(x)` has
output variance ≈ 1. After stacking N blocks, the signal variance grows to ≈ N = 10.

At initialization, gradients flow through:
- The residual paths (variance amplifies N×)
- The branch paths (each layer multiplies variance)

With 10 blocks, this creates unstable gradients and very slow convergence.

### The Fix: Zero-Initialize the Last Layer of Each ResBlock

```python
class ResBlock(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.fc1 = nn.Linear(dim, dim)
        self.bn1 = nn.BatchNorm1d(dim)
        self.fc2 = nn.Linear(dim, dim)
        self.bn2 = nn.BatchNorm1d(dim)
        self.act = nn.ReLU()

        # FIX: zero-initialize fc2 so block initially acts as identity
        nn.init.zeros_(self.fc2.weight)
        nn.init.zeros_(self.fc2.bias)
```

**Why this works**:
- At initialization, `F(x) = fc2(relu(bn1(fc1(x)))) ≈ 0`
- So `output ≈ activation(x + 0) = activation(x)` — the block is near-identity
- Signal variance stays bounded across all 10 blocks
- Training starts with a well-conditioned gradient landscape
- As training proceeds, the fc2 weights grow to learn useful features

This technique (FixUp / ZeroInit) is standard practice for training very deep
residual networks.

---

## Training Config
- Blocks: 10, Hidden dim: 48
- Epochs: 48, Batch size: 32, LR: 0.0005
- Optimizer: Adam

## Deliverables
1. Fixed `model.py` with zero-initialized fc2 in ResBlock
2. `training_results.json` after running `python train.py`
3. `python check_training.py` exits 0
