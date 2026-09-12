"""Evaluation script for multi-label image attribute detection for a content moderation system.

Analysis flags 6 metric-related issues. Read REPORTING_SPEC.md before
modifying anything — some metrics are required by compliance/business and
must not be changed.
"""
import numpy as np
import json
import time
from sklearn.datasets import make_multilabel_classification
from sklearn.metrics import f1_score, precision_score, recall_score


CLASS_NAMES = ["has_person", "has_vehicle", "has_animal", "is_outdoor", "is_nighttime"]
N_CLASSES   = 5

# ISSUE 2 (real bug): threshold not calibrated on validation set
THRESHOLD   = 0.5  # Should be 0.3


def generate_predictions(seed=2):
    """Generate synthetic predictions and ground truth."""
    np.random.seed(seed)
    _, y_true = make_multilabel_classification(
        n_samples=328,
        n_features=20,
        n_classes=N_CLASSES,
        n_labels=2,
        random_state=seed,
    )
    noise = np.random.randn(*y_true.shape) * 0.3
    y_pred_prob = np.clip(y_true.astype(float) + noise, 0, 1)
    return y_true, y_pred_prob


def compute_compliance_accuracy(y_true, y_pred_binary):
    """
    Overall accuracy for compliance report.
    ISSUE 4 (intentional): keep this even though it's misleading — see REPORTING_SPEC.md.
    """
    from sklearn.metrics import accuracy_score
    return float(accuracy_score(y_true.flatten(), y_pred_binary.flatten()))


def compute_business_metric(y_true, y_pred_binary):
    """
    moderation_precision_at_k: precision at k=10 (top-k ranked by confidence).
    ISSUE 5 (intentional): non-standard formula — see REPORTING_SPEC.md §Business Metric.
    """
    recall_scores = recall_score(y_true, y_pred_binary, average=None, zero_division=0)
    precision_scores = precision_score(y_true, y_pred_binary, average=None, zero_division=0)
    mean_recall = float(recall_scores.mean())
    mean_prec   = float(precision_scores.mean())
    fpr = max(0.0, 1.0 - mean_prec)  # approximate FPR as 1 - precision
    # Business formula — contractually defined
    return float(2 * mean_recall - 0.5 * fpr)


def measure_inference_latency(y_pred_prob):
    """
    Measure p95 inference latency.
    ISSUE 6 (intentional): latency is not a model quality metric but must stay — see REPORTING_SPEC.md.
    """
    latencies = []
    np.random.seed(0)
    for _ in range(20):
        t0 = time.perf_counter()
        _ = (y_pred_prob >= THRESHOLD).astype(int)
        latencies.append((time.perf_counter() - t0) * 1000)
    latencies.sort()
    p95_idx = int(len(latencies) * 0.95)
    return float(latencies[p95_idx])


def evaluate():
    """Run evaluation — 3 metrics computed incorrectly, 3 must stay as-is."""
    y_true, y_pred_prob = generate_predictions()

    results = {
        "n_samples": 328,
        "n_classes": N_CLASSES,
        "class_names": CLASS_NAMES,
        "threshold_used": THRESHOLD,
    }

    # ISSUE 1 (real bug): Hamming accuracy masks per-class failure
    from sklearn.metrics import hamming_loss
    y_pred_binary = (y_pred_prob >= THRESHOLD).astype(int)
    # Bug: hamming accuracy appears high even for degenerate all-zero predictor
    ham = 1 - hamming_loss(y_true, y_pred_binary)
    results["primary_metric"] = {"name": "hamming_accuracy", "value": float(ham)}
    results["macro_f1"] = None  # Not computed

    # ISSUE 3 (real bug): confidence intervals missing from all metrics
    # All key metrics should report 95% CI via bootstrap
    results["confidence_intervals"] = None  # Missing — must be added

    y_pred_binary = (y_pred_prob >= THRESHOLD).astype(int)

    # ISSUE 4 (intentional): compliance accuracy — must stay, see REPORTING_SPEC.md
    results["compliance_accuracy"] = compute_compliance_accuracy(y_true, y_pred_binary)

    # ISSUE 5 (intentional): business metric with non-standard formula — must stay
    results["moderation_precision_at_k"] = compute_business_metric(y_true, y_pred_binary)

    # ISSUE 6 (intentional): latency metric — must stay, see REPORTING_SPEC.md
    results["inference_latency_p95_ms"] = measure_inference_latency(y_pred_prob)

    with open("eval_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Evaluation results:")
    for k, v in results.items():
        if k not in ("class_names", "confidence_intervals"):
            print(f"  {k}: {v}")
    return results


if __name__ == "__main__":
    evaluate()
