# ML47: Multi-Task 1/Loss Weighting Instability

## Goal
Fix `trainer.py` so inverse-loss weighting is numerically stable.
Run `python train.py` then `python check_multitask.py` — both must pass.

## Task
Training a **three-task mixed-difficulty learning** with automatic task balancing via 1/loss weighting.
All tasks must converge (val loss < 0.3 each) without gradient explosion.

---

## The Bug: 1/Loss Explodes as Loss → 0

**Location**: `trainer.py` `MultiTaskTrainer.weighted_loss()` — weight computation

### Background: Inverse-Loss Weighting

The idea: tasks that are already well-solved (low loss) should receive lower
gradient weight, so the model focuses on harder tasks.

Weight formula: `w_i = 1 / loss_i`

**Problem 1**: When `loss_i → 0`, `w_i → ∞` → gradient explosion.

**Problem 2**: Using the live (non-detached) loss for weighting introduces
a higher-order gradient: `∂w_i/∂θ = -1/loss_i² * ∂loss_i/∂θ`, which adds
an unstable second-order term to the gradient.

### Current (Buggy) Code

```python
for loss in task_losses:
    # BUG: no epsilon, no detach — explodes as loss -> 0
    w = 1.0 / loss
    weights.append(w)
```

### Correct Fix

```python
for loss in task_losses:
    # FIXED: detach + epsilon prevents explosion
    w = 1.0 / (loss.detach() + self.epsilon)
    weights.append(w)
```

**Why `detach()`**: The weight should be a constant multiplier, not
part of the differentiable computation graph. This removes the pathological
second-order gradient term.

**Why `+ epsilon`**: Prevents `1/0` when any task reaches zero loss.
Use `epsilon = 0.05`.

---

## Training Config
- Tasks: 3 (fast_task, medium_task, slow_task)
- lr: 0.001, Epochs: 88, Batch: 64, epsilon: 0.05

## Deliverables
1. Fixed `trainer.py` with `1/(loss.detach() + epsilon)` weighting
2. `training_results.json` after running `python train.py`
3. `python check_multitask.py` exits 0
