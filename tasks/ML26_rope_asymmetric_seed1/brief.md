# ML26: RoPE Asymmetric Application Bug (Brief)

## Your Task
Fix RoPE in `rope_attention.py` — rotation is applied to keys only, not queries.

Training a **RoPE-based sequence classifier** cannot learn relative position information
because the query vectors are not rotated, breaking RoPE's relative position property.

## What to Fix
- `rope_attention.py`: `RoPEAttention.forward()` — add `q = apply_rope(q, cos, sin)`
- Do NOT modify `train.py`

## Success Criteria
- `python check_rope.py` exits 0
- Validation accuracy > 0.55
