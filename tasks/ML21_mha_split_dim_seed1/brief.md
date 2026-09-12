# ML21: MHA Wrong Split Dimension Bug (Brief)

## Your Task
Fix the multi-head attention reshape in `attention.py`.

Training a **transformer with multi-head attention** fails because Q/K/V are reshaped
incorrectly — splitting the sequence dimension instead of the embedding dimension.

## What to Fix
- `attention.py`: `MultiHeadAttention.forward()` — the reshape and transpose
- Do NOT modify `train.py`

## Success Criteria
- `python check_attention.py` exits 0
- Validation accuracy > 0.55
