# ML35: Temperature Scaling Applied Twice (Double Temperature)

## Goal
Fix the calibration pipeline so temperature scaling is applied **exactly once**.
Run `python train.py` then `python check_calibration.py` — both must pass.

## Task
A **image classification model with temperature scaling** has a double-temperature bug: the temperature `T=1.8`
is applied in `model.forward()` AND again in `evaluator.predict_proba()`.
This makes probabilities over-smooth, keeping ECE (Expected Calibration Error) high.

---

## The Bug: Temperature Scaling Applied in Two Places

### Background: Temperature Scaling

Temperature scaling (Guo et al., 2017) is post-hoc calibration:
```
p(y|x) = softmax(logits / T)
```
With `T > 1`: probabilities become more uniform (less confident).
With `T < 1`: probabilities become sharper (more confident).

### Current (Buggy) Code

**`model.py` — `CalibratedClassifier.forward()`**:
```python
def forward(self, x):
    logits = self.net(x)
    return logits / self.temperature   # BUG: divides by T here
```

**`evaluator.py` — `ModelEvaluator.predict_proba()`**:
```python
def predict_proba(self, x):
    logits = self.model(x)             # already divided by T
    scaled_logits = logits / self.temperature  # BUG: divides by T again
    return F.softmax(scaled_logits, dim=-1)
```

**Effect**: effective temperature = `T² = 1.8² = 3.24`.
Probabilities are much more uniform than intended, ECE stays above 0.15.

### Correct Fix

Remove temperature division from **one** location:

**Option A** — Fix model.py:
```python
def forward(self, x):
    return self.net(x)  # return raw logits, no temperature here
```

**Option B** — Fix evaluator.py:
```python
def predict_proba(self, x):
    logits = self.model(x)
    # logits already temperature-scaled — just apply softmax
    return F.softmax(logits, dim=-1)
```

Either option is correct. After the fix, ECE should drop below 0.10.

---

## Config
- n_samples: 797, epochs: 23, batch: 32, lr: 0.002
- Temperature: 1.8, ECE bins: 15

## Deliverables
1. Fixed `model.py` or `evaluator.py` (remove one temperature division)
2. `calibration_results.json` after running `python train.py`
3. `python check_calibration.py` exits 0
4. Test ECE < 0.10
