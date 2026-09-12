# ML24: CLS Pooling vs Mean Pooling Bug (Brief)

## Your Task
Fix the pooling strategy in `model.py`.

Fine-tuning a **BERT-style model fine-tuned for classification** uses mean pooling, but the
pretrained checkpoint was trained with CLS token pooling. The two
representations are incompatible.

## What to Fix
- `model.py`: `BertClassifier.forward()` — use `enc_out[:, 0, :]` (CLS token)
- Do NOT modify `train.py`

## Success Criteria
- `python check_model.py` exits 0
- Validation accuracy > 0.55
