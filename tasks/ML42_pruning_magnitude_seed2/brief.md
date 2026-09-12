# ML42: Head Pruning Importance Bug (Brief)

## Your Task
Fix `prune.py` — `run()` calls `compute_head_importance_magnitude()` (weight L2 norms)
instead of `compute_head_importance_gradient()` (gradient attribution) for selecting
which 8 of 16 attention heads to prune.

A **multi-layer attention model with head importance pruning** loses more accuracy with magnitude-based pruning because
important heads with small weights get incorrectly removed.

## What to Fix
- `prune.py`: `run()` — replace the `compute_head_importance_magnitude` call with
  `compute_head_importance_gradient(model, X_calib, y_calib, criterion)`
- Set `results["pruning_method"] = "gradient_attribution"`
- Set `results["pruning_ok"] = drop_grad < drop_mag`

## Success Criteria
- `python check_pruning.py` exits 0
- `pruning_method == "gradient_attribution"`
- `gradient_drop < magnitude_drop` (gradient pruning preserves more accuracy)
