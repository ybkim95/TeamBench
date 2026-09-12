# ML5: Data Augmentation Leak (Brief)

## Your Task

Fix the data augmentation pipeline for **image classification with geometric augmentation**.

The pipeline currently has data leakage — the model appears to generalise
better than it truly does.

## Important Warning

Analysis has flagged **5 pipeline steps** as potentially problematic.
**Not all of them are bugs.**

Removing the correct design choices will cause the check to fail.

## Instructions

- Wait for the Planner's instructions
- Apply ONLY the fixes identified by the Planner
- After fixing, run `python augment_pipeline.py` then `python check_pipeline.py`

## Rules
- Fix only `augment_pipeline.py`
- Do not modify `check_pipeline.py`
