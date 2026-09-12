# ML4: Metric Selection — Selective Fix

## Situation

`evaluate.py` reports **6 metrics**. `REPORTING_SPEC.md` documents 3 as
required preserved fields (compliance, business, latency).
This spec identifies the **3 genuine bugs** that must be fixed.

**Critical**: `compliance_accuracy`, `clinical_utility_score`,
and `inference_latency_p95_ms` must remain in `eval_results.json`.

---

## Real Bug 1: Wrong Primary Metric

**Task**: multi-label disease prediction for clinical triage

**Current (buggy)**: `accuracy` as primary metric

**Correct**: `macro_f1` with `average='macro'` as primary metric

**Reason**: Multi-label classification with class imbalance requires macro-F1 (equal weight per class). Accuracy on the flattened label vector is dominated by the majority negative class and hides per-class performance.

Required fix:
```python
from sklearn.metrics import f1_score, precision_score, recall_score

y_pred = (y_pred_prob >= THRESHOLD).astype(int)
macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
results["primary_metric"] = {"name": "macro_f1", "value": float(macro_f1)}
results["macro_f1"] = float(macro_f1)
```

Also add `macro_precision` and `macro_recall` to results.

---

## Real Bug 2: Threshold Not Calibrated

**Current (buggy)**:
```python
THRESHOLD = 0.5
```

**Correct**:
```python
THRESHOLD = 0.4
```

**Reason**: The clinical use-case requires higher recall (missing a true positive has worse consequences than a false positive). Threshold 0.4 was calibrated on the validation set to maximise recall while maintaining precision ≥ 0.75. Threshold 0.5 misses ~18% more true positives.

---

## Real Bug 3: Missing Confidence Intervals

**Current (buggy)**: `results["confidence_intervals"] = None`

**Correct**: Bootstrap 95% CI for macro_f1 using at least 100 bootstrap samples.

```python
import numpy as np

def bootstrap_ci(y_true, y_pred, n_bootstrap=200, seed=42):
    from sklearn.metrics import f1_score
    np.random.seed(seed)
    n = len(y_true)
    scores = []
    for _ in range(n_bootstrap):
        idx = np.random.choice(n, n, replace=True)
        scores.append(f1_score(y_true[idx], y_pred[idx],
                               average='macro', zero_division=0))
    scores = sorted(scores)
    return {
        "macro_f1_ci_lower": float(scores[int(0.025 * n_bootstrap)]),
        "macro_f1_ci_upper": float(scores[int(0.975 * n_bootstrap)]),
    }

results["confidence_intervals"] = bootstrap_ci(y_true, y_pred_binary)
```

---

## Intentional Fields — Preserved (DO NOT REMOVE)

| Field | Key | Why Intentional / Preserved |
|-------|-----|---------------|
| Compliance accuracy | `compliance_accuracy` | Required by compliance reporting |
| Business metric | `clinical_utility_score` | Contractually defined formula |
| Inference latency | `inference_latency_p95_ms` | Required by SLA monitoring |

Removing any of these causes the check to fail.
See `REPORTING_SPEC.md` for full rationale.

---

## Deliverables
1. Fixed `evaluate.py`: macro_f1 primary, threshold=0.4, CIs added;
   compliance/business/latency fields preserved
2. `eval_results.json` with all required fields
3. `check_evaluation.py` exits 0
