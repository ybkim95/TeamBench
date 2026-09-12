# ML27: Normalization Leakage Bug (Brief)

## Your Task
Fix the data pipeline in `pipeline.py`.

A **tabular binary classification dataset** pipeline fits its normalizer (mean/std)
on the full dataset before splitting into train/val/test. This leaks
distribution information from val/test into the training pipeline.

## What to Fix
- `pipeline.py`: `build_pipeline()` — split data FIRST, then fit scaler on `X_train` only
- Apply the train scaler to val/test (do not re-fit on them)
- Set `"fit_on_train_only": True` in the returned dict
- Do NOT modify `train.py`

## Success Criteria
- `python check_pipeline.py` exits 0
- Scaler mean/std computed from training data only
