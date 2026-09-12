# ML30: Augmentation After Normalization Bug (Brief)

## Your Task
Fix the image pipeline in `augment.py`.

The training transform applies `normalize()` FIRST, then color augmentation.
Color jitter and brightness transforms expect pixel values in [0, 1] but
receive normalized values in ~[-2, 2].

## What to Fix
- `augment.py`: `train_transform()` — move `normalize()` to be the LAST step
- Update `get_pipeline_order()` to return the correct order string ending with `"normalize"`
- Do NOT modify `train.py`

## Success Criteria
- `python check_augment.py` exits 0
- `get_pipeline_order()` returns a string ending with `"normalize"`
