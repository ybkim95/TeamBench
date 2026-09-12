# ML16: Contrastive False Negatives (Brief)

## Your Task
Fix the NT-Xent contrastive loss in `nt_xent_loss.py`.

Training a **SimCLR tabular encoder** with SimCLR is producing representations that
are WORSE than random -- because the contrastive loss has a bug that treats
positive pairs as negatives.

## Symptoms
- Linear probe accuracy near random-chance even after many epochs
- Loss decreases but representations don't cluster by class

## What to Fix
- `nt_xent_loss.py`: the `neg_mask` construction in `nt_xent_loss()`
- The positive pair must be excluded from the negative denominator
- The Planner has the exact fix

## Success Criteria
- `python check_training.py` exits 0
- Linear probe accuracy > 0.55
