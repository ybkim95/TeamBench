# ML44: GAN Minimax vs Non-Saturating Loss

## Goal
Fix `gan.py` so the generator uses the non-saturating loss.
Run `python train.py` then `python check_gan.py` — both must pass.

## Task
Training a GAN on **low-dimensional density estimation** (4D).
The generator must achieve >0.5 coverage of the real data modes.

---

## The Bug: Minimax Generator Loss Saturates

**Location**: `gan.py` `GAN.generator_loss()` — wrong loss formulation

### Background

The original GAN paper (Goodfellow et al. 2014) defines the minimax game:

```
min_G max_D  E[log D(x)] + E[log(1 - D(G(z)))]
```

The generator minimizes `E[log(1 - D(G(z)))]`.

**Problem**: When the discriminator is good early in training (D(G(z)) ≈ 0):
```
d/dz log(1 - D(G(z))) ≈ 0    # gradient vanishes!
```

The **non-saturating** alternative (also from the same paper) is:
```
min_G  -E[log D(G(z))]
```

This has gradient `-1/D(G(z))` — large and stable even when D(G(z)) ≈ 0.

### Current (Buggy) Code

```python
def generator_loss(self, fake: torch.Tensor) -> torch.Tensor:
    d_fake = self.D(fake)
    # BUG: minimax — saturates when d_fake → 0
    loss = torch.log(1 - d_fake + 1e-8).mean()
    return loss
```

### Correct Fix

```python
def generator_loss(self, fake: torch.Tensor) -> torch.Tensor:
    d_fake = self.D(fake)
    # Non-saturating: strong gradients even when D is confident
    loss = -torch.log(d_fake + 1e-8).mean()
    return loss
```

---

## Training Config
- lr_G: 0.0002, lr_D: 0.0001, Epochs: 214, Batch: 32

## Deliverables
1. Fixed `gan.py` with non-saturating generator loss
2. `training_results.json` after running `python train.py`
3. `python check_gan.py` exits 0
