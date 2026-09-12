# ML50: Active Learning Uncalibrated Uncertainty Bug (Brief)

## Your Task
Fix the active learning strategy in `query_strategy.py`.

**pool-based active learning classifier** performs poorly because `EntropyStrategy` uses raw
softmax entropy, which is unreliable for overconfident neural networks.
The `MCDropoutStrategy` (BALD) correctly estimates epistemic uncertainty
but needs to be properly implemented and used.

## Symptoms
- Active learning with entropy barely outperforms random sampling
- Model selects easy/boundary-adjacent samples, not informative hard samples
- AUC of learning curve is low

## What to Fix
- `query_strategy.py`: Complete `MCDropoutStrategy.select()` to use BALD score
  (run T forward passes with `model.train()`, compute `H_mean - E[H]`)
- The strategy is already structured — implement the BALD computation
- Do NOT modify `model.py`

## Success Criteria
- `python check_active.py` exits 0
- MC Dropout AUC > 0.65 and better than entropy AUC
