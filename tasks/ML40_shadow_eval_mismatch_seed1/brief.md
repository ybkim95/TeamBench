# ML40: Shadow Deployment Mode Mismatch (Brief)

## Your Task
Fix `shadow_eval.py` — the shadow model is in `train()` mode during evaluation
while the production model is in `eval()` mode. This unfair comparison (dropout=0.3
degrades shadow predictions) makes the shadow model look worse than it is.

## What to Fix
- `shadow_eval.py`: `run_shadow_evaluation()` — change `shadow_model.train()` to `shadow_model.eval()`
- Update `results["eval_mode_match"] = True` and `results["shadow_in_eval"] = True`

## Success Criteria
- `python check_shadow.py` exits 0
- `eval_mode_match = True`
- Shadow and production models both evaluated in eval() mode
