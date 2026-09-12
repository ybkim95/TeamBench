# ML34: Dataset Version Mismatch Bug (Brief)

## Your Task
Fix the dataset loader in `dataset.py`.

A **medical image annotation with expert reannotation in v2.1** trains on v2.1 labels (corrected) but
evaluates against v2.0 labels (original, ~12% contain errors).
This version mismatch causes the model to be evaluated against stale labels.

## What to Fix
- `dataset.py`: `load_eval_labels()` — call `make_labels_v2_1()` instead of `make_labels_v2_0()`
- Update `get_label_versions_match()` to return `True`
- Do NOT modify `train.py`

## Success Criteria
- `python check_dataset.py` exits 0
- `versions_match=True` in training_results.json
- `label_mismatch_rate` near 0 in training_results.json
