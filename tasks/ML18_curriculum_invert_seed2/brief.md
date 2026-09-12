# ML18: Curriculum Learning Pacing Inverted (Brief)

## Your Task
Fix the pacing function in `curriculum.py`.

Training a **regression model with curriculum** with curriculum learning is starting with ALL
the data and REDUCING it over time — exactly backwards from what curriculum
learning should do.

## Symptoms
- Model sees hard examples from epoch 0 (no warm-up)
- Final epochs use only 30% of data (training data shrinks)
- `pacing_start` ≈ 1.0, `pacing_end` ≈ 0.3 in training_results.json

## What to Fix
- `curriculum.py`: `pacing_function()` — one-line fix to the fraction formula
- Do NOT modify `compute_difficulty_scores()` or `get_curriculum_subset()`

## Success Criteria
- `python check_training.py` exits 0
- Pacing starts at ~0.3 and ends at ~1.0
