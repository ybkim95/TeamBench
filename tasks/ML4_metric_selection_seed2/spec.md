# ML4: Metric Selection — Selective Fix

## Situation

`evaluate.py` reports **6 metrics**. `REPORTING_SPEC.md` documents 3 as
required preserved fields (compliance, business, latency).
This spec identifies the **3 genuine bugs** that must be fixed.

**Critical**: `compliance_accuracy`, `moderation_precision_at_k`,
and `inference_latency_p95_ms` must remain in `eval_results.json`.

---

## Real Bug 1: Wrong Primary Metric

**Task**: multi-label image attribute detection for a content moderation system

**Current (buggy)**: `hamming_accuracy` as primary metric

**Correct**: `macro_f1` with `average='macro'` as primary metric

**Reason**: Hamming accuracy (1 - hamming_loss) appears high even for bad models because most label slots are True Negatives. With 5 binary labels and sparse positives, a model predicting all-zeros achieves 80%+ Hamming accuracy. Macro-F1 correctly penalises such degenerate behaviour.

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
THRESHOLD = 0.3
```

**Reason**: Positive attributes are sparse in the moderation dataset (~15% prevalence). Threshold 0.3 was calibrated to recover these sparse positives. At threshold 0.5 the model misses 35% of true positives, making moderation ineffective.

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
| Business metric | `moderation_precision_at_k` | Contractually defined formula |
| Inference latency | `inference_latency_p95_ms` | Required by SLA monitoring |

Removing any of these causes the check to fail.
See `REPORTING_SPEC.md` for full rationale.

---

## Deliverables
1. Fixed `evaluate.py`: macro_f1 primary, threshold=0.3, CIs added;
   compliance/business/latency fields preserved
2. `eval_results.json` with all required fields
3. `check_evaluation.py` exits 0
