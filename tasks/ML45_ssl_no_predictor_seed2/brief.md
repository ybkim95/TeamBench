# ML45: BYOL Missing Predictor Bug (Brief)

## Your Task
Fix the BYOL loss in `byol.py` to apply the predictor MLP.

Training **tabular data self-supervised learning** with BYOL collapses because the online
network does not apply its predictor MLP, removing the asymmetry that
prevents mode collapse.

## Symptoms
- Linear probe accuracy near random chance
- Loss decreases but representations have near-zero variance
- All samples map to nearly identical representations

## What to Fix
- `byol.py`: `BYOL.loss()` — apply `self.predictor` to `online_z1` and `online_z2`
- Do NOT modify `train.py`

## Success Criteria
- `python check_byol.py` exits 0
- Linear probe accuracy > 0.55
