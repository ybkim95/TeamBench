# ML23: Cross-Attention Q/K/V Swap Bug (Brief)

## Your Task
Fix cross-attention in `cross_attention.py` — Q and K/V sources are swapped.

Training a **encoder-decoder translation model** fails because the cross-attention
uses Q from the encoder and K/V from the decoder instead of the correct order.

## What to Fix
- `cross_attention.py`: `CrossAttention.forward()` — Q from decoder, K/V from encoder
- Do NOT modify `train.py`

## Success Criteria
- `python check_cross_attn.py` exits 0
- Validation accuracy > 0.40
