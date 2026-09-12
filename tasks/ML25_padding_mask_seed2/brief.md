# ML25: Missing Padding Mask Bug (Brief)

## Your Task
Fix `model.py` — causal attention is missing the padding mask.

Training a **autoregressive model with padded batches** with variable-length padded batches
is polluted because PAD token positions are not masked out of attention.

## What to Fix
- `model.py`: `CausalAttention.forward()` — apply `padding_mask` to attention weights
- Mask key positions that are PAD: `attn.masked_fill(padding_mask.unsqueeze(1).unsqueeze(2), -inf)`
- Do NOT modify `train.py`

## Success Criteria
- `python check_model.py` exits 0
- Validation accuracy > 0.50
