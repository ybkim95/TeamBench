# ML19: Causal Mask Off-by-One Bug (Brief)

## Your Task
Fix the causal attention mask in `model.py`.

Training a **decoder-only transformer language model** is failing because the causal mask
blocks each token from attending to itself.

## Symptoms
- Model converges slowly or gets stuck
- Each token cannot incorporate its own embedding through self-attention
- Attention patterns are incorrect (diagonal blocked)

## What to Fix
- `model.py`: `CausalSelfAttention.__init__()` — the `diagonal` parameter
- Do NOT modify `train.py`

## Success Criteria
- `python check_model.py` exits 0
- Validation accuracy > 0.55
