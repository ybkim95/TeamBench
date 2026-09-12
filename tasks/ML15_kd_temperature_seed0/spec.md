# ML15: Knowledge Distillation Temperature Asymmetry

## Goal
Fix `train.py` so knowledge distillation uses temperature correctly.
Run `python train.py` then `python check_training.py`.

## Task
Distilling a **deep ResNet teacher** into a **small MLP student**
with temperature T=4.0 and alpha=0.9 (KD weight).

---

## The Bug: Asymmetric Temperature in KD Loss

**Location**: `train.py`, `kd_loss()` function

### Background: Knowledge Distillation

KD trains a student to match the teacher's soft output distribution.
Temperature T controls how "soft" the teacher's distribution is:
- High T → softer distribution → more information in the dark knowledge
- The student must use the SAME temperature to match the teacher's scale

### Bug 1: Student Logits Not Divided by Temperature

**Current (buggy)**:
```python
teacher_probs = F.softmax(teacher_logits / T, dim=-1)       # T=4.0 applied
student_log_probs = F.log_softmax(student_logits, dim=-1)   # BUG: no temperature!
kd = F.kl_div(student_log_probs, teacher_probs, reduction="batchmean")
```

**Problem**: Teacher distribution is computed at temperature T=4.0 (very soft),
but student distribution is at temperature 1 (sharp). The KL divergence compares
distributions at different "scales" — the student is penalized for not being as
sharp as T=1, while the teacher target is soft as T=4.0.

### Bug 2: Missing T² Scaling Factor

**Current (buggy)**:
```python
kd = F.kl_div(student_log_probs, teacher_probs, reduction="batchmean")
# Missing: kd = kd * (T * T)
```

**Problem**: When both softmax inputs are divided by T, the gradients w.r.t.
the original logits are scaled by 1/T². Without compensating, the KD loss
contributes T²=16× smaller gradients than the hard CE loss.
With alpha=0.9 weighting the KD loss, its effective contribution is
`alpha/T² = 0.9/16 ≈ 0.0563` — negligible.

### Correct Code

```python
def kd_loss(student_logits, teacher_logits, targets, T=4.0, alpha=0.9):
    teacher_probs = F.softmax(teacher_logits / T, dim=-1)
    student_log_probs = F.log_softmax(student_logits / T, dim=-1)  # same T
    kd = F.kl_div(student_log_probs, teacher_probs, reduction="batchmean")
    kd = kd * (T * T)  # restore gradient magnitude
    ce = F.cross_entropy(student_logits, targets)
    return alpha * kd + (1 - alpha) * ce
```

---

## Deliverables
1. Fixed `train.py` with symmetric temperature and T² scaling
2. `training_results.json` after running `python train.py`
3. `python check_training.py` exits 0
