# ML18: Curriculum Learning Pacing Function Inverted

## Goal
Fix `curriculum.py` so the pacing function correctly schedules easy-to-hard training.
Run `python train.py` then `python check_training.py`.

## Task
Training a **regression model with curriculum** with curriculum learning.
Start fraction: 0.3 (begin with 30% of data, easiest samples).

---

## The Bug: Pacing Function is Inverted

**Location**: `curriculum.py`, `pacing_function()`

### Curriculum Learning Background

Curriculum learning trains on easy examples first, gradually adding harder ones:
- Epoch 0: Use only `start_fraction=0.3` of data (the easiest 30%)
- Intermediate: Linearly increase the fraction
- Final epoch: Use 100% of data (all samples, including hardest)

The "pacing function" controls what fraction of data is accessible at each epoch.

### Current (Buggy) Code

```python
def pacing_function(epoch, total_epochs, start_fraction=0.3):
    progress = epoch / max(total_epochs - 1, 1)
    # BUG: Inverted — DECREASES from 1.0 to start_fraction
    fraction = 1.0 - (1.0 - start_fraction) * progress
    return float(max(0.01, min(1.0, fraction)))
```

**What happens**:
| Epoch | progress | Buggy fraction | Correct fraction |
|-------|----------|---------------|-----------------|
| 0     | 0.0      | 1.000         | 0.300 |
| 25%   | 0.25     | 0.825         | 0.475 |
| 50%   | 0.50     | 0.650         | 0.650 |
| 100%  | 1.0      | 0.300         | 1.000 |

With the bug:
- Training starts with ALL data (hard examples thrown in immediately)
- Training ENDS with only 30% data (loses most training signal)
- The final epochs train on a tiny, easy-only subset — model forgets hard patterns

### Correct Code

```python
def pacing_function(epoch, total_epochs, start_fraction=0.3):
    progress = epoch / max(total_epochs - 1, 1)
    # Correct: INCREASES from start_fraction to 1.0
    fraction = start_fraction + (1.0 - start_fraction) * progress
    return float(max(0.01, min(1.0, fraction)))
```

This starts at 0.3 (only the easiest 30% of samples) and
linearly increases to 1.0 by the final epoch.

---

## How Difficulty is Computed
`compute_difficulty_scores()` in `curriculum.py` computes per-sample difficulty
as the distance from each sample to its class centroid. Samples far from their
class are "harder" (more ambiguous). This function is CORRECT — do not modify it.

---

## Deliverables
1. Fixed `curriculum.py` with correct `pacing_function()`
2. `training_results.json` after running `python train.py`
3. `python check_training.py` exits 0
