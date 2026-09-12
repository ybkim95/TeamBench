# ML50: Active Learning Uncalibrated Uncertainty

## Goal
Fix `query_strategy.py` so active learning uses MC Dropout (BALD) instead of
raw entropy. Run `python train.py` then `python check_active.py` — both must pass.

## Task
**active learning for imbalanced classification** with 1200 unlabeled pool, 25 initial labels,
25 queries per round, 10 rounds.
MC Dropout AUC must exceed 0.65 AND outperform raw entropy selection.

---

## The Bug: Entropy Selection on Overconfident Model

**Location**: `query_strategy.py` `EntropyStrategy.select()` — raw softmax entropy

### Background

Active learning selects which unlabeled samples to label next, aiming for
maximum informativeness. **Entropy selection** picks samples where the model
is most uncertain (high entropy of softmax output).

**Problem**: Neural networks are systematically overconfident.
Their softmax entropy does NOT reflect true uncertainty:
- Samples near the true decision boundary may have LOW entropy (high confidence, wrong)
- Out-of-distribution samples may have HIGH entropy despite being uninformative
- The model's confidence calibration degrades in low-data regimes (active learning!)

### Fix: MC Dropout (BALD — Bayesian Active Learning by Disagreement)

1. Run T=`10` stochastic forward passes with **dropout enabled** (`model.train()`)
2. Compute BALD score = epistemic uncertainty:

```python
all_probs = stack([softmax(model(X)) for _ in range(T)])  # (T, N, C)
mean_probs = all_probs.mean(0)                             # (N, C)

H_mean = entropy(mean_probs)        # total uncertainty
E_H = mean(entropy(all_probs))      # expected aleatoric uncertainty
bald = H_mean - E_H                 # epistemic uncertainty only
```

3. Select top-n samples by BALD score.

The `MCDropoutStrategy` class is already defined in `query_strategy.py` — the fix
is to use it in `train.py` instead of `EntropyStrategy`.

But the PRIMARY fix is completing the `MCDropoutStrategy.select()` implementation
if not complete, and ensuring `train.py` evaluates with it.

---

## Training Config
- Dropout rate: 0.3, MC samples: 10
- lr: 0.001, train epochs per round: 22

## Deliverables
1. Fixed `query_strategy.py` with complete `MCDropoutStrategy`
2. `training_results.json` after running `python train.py`
3. `python check_active.py` exits 0
