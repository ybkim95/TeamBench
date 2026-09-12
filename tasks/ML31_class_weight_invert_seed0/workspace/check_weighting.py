"""Validate class weight inversion fix."""
import json
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from weighting import make_imbalanced_dataset, compute_class_weights, N_CLASSES


def check_minority_has_highest_weight():
    """Verify minority class (last) has higher weight than majority class (first)."""
    X, y = make_imbalanced_dataset(n=500, seed=42)
    n_train = int(len(y) * 0.8)
    y_train = y[:n_train]
    weights = compute_class_weights(y_train, n_classes=N_CLASSES)

    if weights[-1] <= weights[0]:
        return False, (
            f"Minority class weight ({weights[-1]:.4f}) <= majority class weight ({weights[0]:.4f}) — "
            f"weights are not inverted"
        )
    return True, (
        f"Minority class weight ({weights[-1]:.4f}) > majority class weight ({weights[0]:.4f}) — correct"
    )


def check_weights_inverse_to_counts():
    """Verify weights are approximately inversely proportional to counts."""
    y = np.array([0] * 100 + [1] * 20 + [2] * 5)
    np.random.RandomState(0).shuffle(y)
    weights = compute_class_weights(y, n_classes=3)

    # Class 2 (rarest) should have highest weight, class 0 (most common) lowest
    if not (weights[2] > weights[1] > weights[0]):
        return False, (
            f"Weights not inversely ordered: w0={weights[0]:.4f}, "
            f"w1={weights[1]:.4f}, w2={weights[2]:.4f} (expected w2>w1>w0)"
        )
    return True, f"Weights inversely ordered: w0={weights[0]:.4f}, w1={weights[1]:.4f}, w2={weights[2]:.4f}"


def check_weights_sum_to_one():
    """Verify weights sum to approximately 1 (normalized)."""
    y = np.array([0] * 80 + [1] * 15 + [2] * 5)
    weights = compute_class_weights(y, n_classes=3)
    total = weights.sum()
    if abs(total - 1.0) > 0.01:
        return False, f"Weights sum to {total:.6f}, expected ~1.0"
    return True, f"Weights sum to {total:.6f} ~= 1.0"


def check_source_uses_inverse():
    """Verify weighting.py uses 1/counts (or equivalent) not counts/sum."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weighting.py')) as f:
        src = f.read()
    import re
    # Must NOT have: weights = counts / sum (frequency weighting)
    if re.search(r'weights\s*=\s*counts\s*/\s*\(?\s*counts\.sum', src):
        return False, "Still using frequency weights: counts / counts.sum()"
    # Should have: 1.0 / counts (or similar inverse)
    has_inverse = (
        '1.0 / ' in src or
        '1 / ' in src or
        '1.0/counts' in src or
        '/ counts' in src and 'sum' not in src.split('/ counts')[0].split('\n')[-1]
    )
    if not has_inverse:
        return False, "No inverse frequency pattern (1/counts) found in weighting.py"
    return True, "Inverse frequency weighting (1/counts) found"


def check_training_results_minority_upweighted():
    """Verify training_results.json shows minority_upweighted=True."""
    if not os.path.exists("training_results.json"):
        return False, "training_results.json not found"
    with open("training_results.json") as f:
        res = json.load(f)
    if not res.get("minority_upweighted", False):
        return False, f"minority_upweighted=False, class_weights={res.get('class_weights')}"
    return True, f"minority_upweighted=True, weights={res.get('class_weights')}"


def check_minority_recall():
    """Verify minority class recall > 0.30."""
    if not os.path.exists("training_results.json"):
        return False, "training_results.json not found"
    with open("training_results.json") as f:
        res = json.load(f)
    recall = res.get("final_minority_recall", 0)
    if recall <= 0.30:
        return False, f"Minority class recall too low: {recall:.4f} (expected > 0.30)"
    return True, f"Minority class recall: {recall:.4f} > 0.30"


def check_weight_ratio():
    """Verify weight ratio minority/majority reflects imbalance ratio."""
    X, y = make_imbalanced_dataset(n=1000, seed=42)
    n_train = int(len(y) * 0.8)
    y_train = y[:n_train]
    weights = compute_class_weights(y_train, n_classes=N_CLASSES)

    counts = np.bincount(y_train, minlength=N_CLASSES).astype(float)
    # Expected ratio: (count_majority / count_minority)
    expected_ratio_approx = counts[0] / (counts[-1] + 1e-8)
    actual_ratio = weights[-1] / (weights[0] + 1e-8)

    # Actual weight ratio should be in the same ballpark as count ratio
    if actual_ratio < 1.5:
        return False, f"Weight ratio minority/majority too small: {actual_ratio:.2f} (counts ratio: {expected_ratio_approx:.2f})"
    return True, f"Weight ratio minority/majority: {actual_ratio:.2f} (counts ratio: {expected_ratio_approx:.2f})"


def check_no_zero_weights():
    """Verify no class has zero weight."""
    y = np.array([0] * 100 + [1] * 10 + [2] * 2)
    weights = compute_class_weights(y, n_classes=3)
    if (weights == 0).any():
        return False, f"Zero weight found: {weights}"
    if (weights < 0).any():
        return False, f"Negative weight found: {weights}"
    return True, f"All weights positive: {weights}"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    acc = res.get("final_val_acc", 0)
    recall = res.get("final_minority_recall", 0)
    weights = res.get("class_weights", [])
    print(f"Final val_acc: {acc:.4f}, minority_recall: {recall:.4f}, weights: {weights}")

    checks = [
        check_minority_has_highest_weight,
        check_weights_inverse_to_counts,
        check_weights_sum_to_one,
        check_source_uses_inverse,
        check_training_results_minority_upweighted,
        check_minority_recall,
        check_weight_ratio,
        check_no_zero_weights,
    ]

    all_pass = True
    for fn in checks:
        ok, msg = fn()
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {fn.__name__}: {msg}")
        if not ok:
            all_pass = False

    if not res.get("converged", False):
        print(f"FAIL: Model did not converge (minority_recall={recall:.4f} < 0.30)")
        all_pass = False

    if all_pass:
        print("PASS")
    return all_pass


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
