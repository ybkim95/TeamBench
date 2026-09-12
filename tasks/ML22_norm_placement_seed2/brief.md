# ML22: LayerNorm Broken Hybrid Bug (Brief)

## Your Task
Fix the LayerNorm placement in `transformer.py`.

Training a **deep transformer encoder** is unstable because the transformer block
uses a broken mix of pre-norm and post-norm that is neither consistent pattern.

## What to Fix
- `transformer.py`: `TransformerBlock.forward()` — make norm placement consistent
- Use either pure pre-norm OR pure post-norm (pre-norm recommended)
- Do NOT modify `train.py`

## Success Criteria
- `python check_transformer.py` exits 0
- Validation accuracy > 0.55
