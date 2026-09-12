# ML20: Sinusoidal PE Frequency Bug (Brief)

## Your Task
Fix the sinusoidal positional encoding in `positional_encoding.py`.

Training a **position-sensitive sequence model** uses incorrect frequency bands in the
positional encoding — the `arange` step parameter is wrong.

## What to Fix
- `positional_encoding.py`: `SinusoidalPE.__init__()` — the `step` in `torch.arange`
- Do NOT modify `train.py`

## Success Criteria
- `python check_pe.py` exits 0
- Validation accuracy > 0.55
