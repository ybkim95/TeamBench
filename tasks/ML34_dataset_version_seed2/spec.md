# ML34: Dataset Version Mismatch (Train v2.1, Eval v2.0)

## Goal
Fix `dataset.py` so both training and evaluation use the same label version (v2.1).
Run `python train.py` then `python check_dataset.py` — both must pass.

## Task
A **medical image annotation with expert reannotation in v2.1** went through an annotation correction process:
- **v2.0**: Original crowd-sourced labels (~12% contain errors)
- **v2.1**: Expert-corrected labels (ground truth used for training)

The training pipeline correctly uses v2.1 labels, but evaluation uses v2.0.

---

## The Bug: Evaluation Uses Stale v2.0 Labels

**Location**: `load_eval_labels()` in `dataset.py`

### Background

Dataset versioning is critical in ML pipelines. When annotations are updated:

1. Training MUST use the latest version (v2.1 — corrected)
2. Evaluation MUST also use the latest version
3. If they differ, ~12% of eval samples will have wrong ground truth

### Current (Buggy) Code

```python
def load_eval_labels(n, seed):
    return make_labels_v2_0(n, seed)   # BUG: stale v2.0 labels
```

**Effect**:
- Model predicts the v2.1-correct label for 12% of re-annotated examples
- Evaluator compares against v2.0 (stale) label → always wrong
- True model accuracy is underreported by ~12%
- Model appears worse than it is on the re-annotated subset

### Correct Fix

```python
def load_eval_labels(n, seed):
    return make_labels_v2_1(n, seed)   # same version as training
```

Also update:
```python
def get_label_versions_match() -> bool:
    return True  # train and eval now use same version
```

### Version Comparison

| Split | Buggy version | Fixed version |
|-------|--------------|---------------|
| Train | v2.1 (correct) | v2.1 (correct) |
| Eval  | v2.0 (stale)   | v2.1 (correct) |
| Mismatch rate | ~12% | 0% |

---

## Training Config
- Classes: 2, LR: 0.002, Epochs: 22, Batch: 32

## Deliverables
1. Fixed `dataset.py`: `load_eval_labels()` uses `make_labels_v2_1`
2. Updated `get_label_versions_match()` returns `True`
3. `training_results.json` after running `python train.py`
4. `python check_dataset.py` exits 0
