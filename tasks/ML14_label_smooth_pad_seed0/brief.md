# ML14: Label Smoothing PAD Bug (Brief)

## Your Task
Fix `smooth_loss.py` — the label smoothing implementation has two related bugs
involving the PAD token.

Training a **sequence-to-sequence model** is not learning correctly because the loss
function treats PAD (index 0) like a real output token.

## What to Fix
- `smooth_loss.py`: `LabelSmoothingLoss.forward()`
- Two bugs: (1) PAD gets smoothing mass, (2) PAD positions not masked
- The Planner has the exact fix details

## Success Criteria
- `python check_training.py` exits 0
- Validation accuracy > 0.60
