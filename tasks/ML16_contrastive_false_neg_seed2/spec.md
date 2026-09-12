# ML16: Contrastive False Negatives (SimCLR)

## Goal
Fix `nt_xent_loss.py` so the NT-Xent contrastive loss correctly excludes
positive pairs from the negative set. Run `python train.py` then `python check_training.py`.

## Task
Training a **SimCLR tabular encoder** with SimCLR-style contrastive learning.
Temperature: 0.1, Batch size: 32.

---

## The Bug: Positive Pair Included in Negative Denominator

**Location**: `nt_xent_loss.py`, `nt_xent_loss()` -- the `neg_mask` construction

### NT-Xent Loss Background

For a batch of N samples, each augmented twice (z1[i], z2[i] = positive pair):

```
NT-Xent(i) = -log(
    exp(sim(z1[i], z2[i]) / T) /
    sum_{k!=i} exp(sim(z1[i], z_k) / T)   <-- sum over negatives ONLY
)
```

The denominator sums over ALL other views EXCEPT the positive partner z2[i].

### Current (Buggy) Code

```python
# BUG: Only excludes diagonal (self-similarity)
# Does NOT exclude the positive partner
neg_mask = ~torch.eye(2 * N, dtype=torch.bool, device=z.device)
```

**What this does wrong**: For z1[i], the negative set includes z2[i]
(which is z1[i]'s positive partner). The loss then PENALIZES having
high similarity with z2[i] -- which is the exact opposite of what we want!

This is called a **false negative**: a sample that should be a positive
(same instance, different augmentation) is incorrectly treated as a negative.

### Correct Code

```python
# Exclude BOTH diagonal (self) AND positive pairs
neg_mask = ~torch.eye(2 * N, dtype=torch.bool, device=z.device) & ~pos_mask
```

Where `pos_mask` marks the positive pairs:
```python
pos_mask = torch.zeros(2 * N, 2 * N, dtype=torch.bool, device=z.device)
for i in range(N):
    pos_mask[i, i + N] = True
    pos_mask[i + N, i] = True
```

### Impact

With the buggy mask:
- The loss maximizes similarity to random negatives
- AND minimizes similarity to the actual positive partner
- Result: the encoder learns to push apart augmented views of the same sample

With the fix:
- The loss maximizes similarity to the positive partner
- AND minimizes similarity to all other samples
- Result: the encoder learns augmentation-invariant representations

---

## Deliverables
1. Fixed `nt_xent_loss.py` with correct negative mask
2. `training_results.json` after running `python train.py`
3. `python check_training.py` exits 0
