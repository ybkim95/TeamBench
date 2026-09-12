# ML28: Multi-Label Stratification Bug (Brief)

## Your Task
Fix the dataset splitter in `splitter.py`.

A **multi-label text tagging dataset** with 4 labels uses single-label
stratification (`y[:, 0]`) when splitting train/val. This ignores the
joint co-occurrence distribution of all 4 labels.

## What to Fix
- `splitter.py`: `stratified_split()` — use composite key of all 4 labels
- Set `"stratify_all_labels": True` in returned dict
- Do NOT modify `train.py`

## Success Criteria
- `python check_splitter.py` exits 0
- All 4 label rates balanced across train/val
