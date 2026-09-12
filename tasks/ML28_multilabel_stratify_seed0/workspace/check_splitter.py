"""Validate multi-label stratification fix."""
import json
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from splitter import make_multilabel_dataset, stratified_split


def check_stratify_all_labels_flag():
    """Verify stratify_all_labels is True in returned dict."""
    X, y = make_multilabel_dataset(n=300, seed=42)
    splits = stratified_split(X, y, val_frac=0.2, seed=0)
    if not splits.get("stratify_all_labels", False):
        return False, "stratify_all_labels is False — single-label bug not fixed"
    return True, "stratify_all_labels=True confirmed"


def check_source_not_uses_single_label():
    """Verify splitter.py uses composite label key, not y[:, 0]."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'splitter.py')) as f:
        src = f.read()
    if 'y[:, 0]' in src and 'stratify_key' in src:
        # Check if it's still the buggy assignment
        import re
        if re.search(r'stratify_key\s*=\s*y\[:, 0\]', src):
            return False, "stratify_key = y[:, 0] still present (single-label bug)"
    return True, "Single-label stratification pattern not found"


def check_composite_key_present():
    """Verify a composite key or all-label stratification is present."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'splitter.py')) as f:
        src = f.read()
    has_composite = (
        "join" in src or
        "label_keys" in src or
        "stratify_all" in src or
        ("y[:, i]" in src and "for i in range" in src) or
        "y.tolist" in src or
        "tuple" in src and "zip" in src
    )
    if not has_composite:
        return False, "No composite label key strategy found in splitter.py"
    return True, "Composite label key strategy found"


def check_label_distribution_balanced():
    """Verify all labels are balanced across train/val split."""
    X, y = make_multilabel_dataset(n=600, seed=42)
    splits = stratified_split(X, y, val_frac=0.2, seed=0)

    y_train = splits["y_train"]
    y_val = splits["y_val"]

    train_rates = y_train.mean(axis=0)
    val_rates = y_val.mean(axis=0)

    max_deviation = np.abs(train_rates - val_rates).max()
    if max_deviation > 0.15:
        return False, (
            f"Label distribution imbalance: max_deviation={max_deviation:.4f} "
            f"(train_rates={train_rates}, val_rates={val_rates})"
        )
    return True, f"Label distributions balanced: max_dev={max_deviation:.4f}"


def check_rare_label_distribution():
    """Verify the rare label (3) is distributed properly."""
    X, y = make_multilabel_dataset(n=800, seed=42)
    splits = stratified_split(X, y, val_frac=0.2, seed=0)

    y_train = splits["y_train"]
    y_val = splits["y_val"]

    # Rare label (last one, ~10% positive)
    rare_train = y_train[:, -1].mean()
    rare_val = y_val[:, -1].mean()

    if abs(rare_train - rare_val) > 0.10:
        return False, (
            f"Rare label rate differs: train={rare_train:.4f}, val={rare_val:.4f} "
            f"(diff={abs(rare_train - rare_val):.4f})"
        )
    return True, f"Rare label balanced: train={rare_train:.4f}, val={rare_val:.4f}"


def check_split_sizes():
    """Verify split sizes are reasonable."""
    X, y = make_multilabel_dataset(n=500, seed=42)
    splits = stratified_split(X, y, val_frac=0.2, seed=0)

    n_train = splits["n_train"]
    n_val = splits["n_val"]
    total = n_train + n_val

    if total != 500:
        return False, f"Split sizes don't add up: {n_train} + {n_val} = {total} != 500"
    if n_val < 50 or n_val > 200:
        return False, f"Val size {n_val} out of expected range [50, 200]"
    return True, f"Split sizes OK: train={n_train}, val={n_val}"


def check_cooccurrence_preserved():
    """Verify co-occurring label pairs have similar rates in train/val."""
    X, y = make_multilabel_dataset(n=800, seed=42)
    splits = stratified_split(X, y, val_frac=0.2, seed=0)

    y_train = splits["y_train"]
    y_val = splits["y_val"]

    # Check label_0 AND label_1 co-occurrence (correlated pair)
    co_train = (y_train[:, 0] * y_train[:, 1]).mean()
    co_val = (y_val[:, 0] * y_val[:, 1]).mean()

    if abs(co_train - co_val) > 0.15:
        return False, (
            f"Co-occurrence of labels 0&1 differs: train={co_train:.4f}, "
            f"val={co_val:.4f} (diff={abs(co_train - co_val):.4f})"
        )
    return True, f"Co-occurrence preserved: train={co_train:.4f}, val={co_val:.4f}"


def check_reproducibility():
    """Verify same seed gives same split."""
    X, y = make_multilabel_dataset(n=300, seed=42)
    s1 = stratified_split(X, y, val_frac=0.2, seed=7)
    s2 = stratified_split(X, y, val_frac=0.2, seed=7)
    if not np.array_equal(s1["X_train"], s2["X_train"]):
        return False, "Same seed gives different split (non-deterministic)"
    return True, "Split is deterministic"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    f1 = res.get("final_val_f1", 0)
    print(f"Final val F1: {f1:.4f}")

    checks = [
        check_stratify_all_labels_flag,
        check_source_not_uses_single_label,
        check_composite_key_present,
        check_label_distribution_balanced,
        check_rare_label_distribution,
        check_split_sizes,
        check_cooccurrence_preserved,
        check_reproducibility,
    ]

    all_pass = True
    for fn in checks:
        ok, msg = fn()
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {fn.__name__}: {msg}")
        if not ok:
            all_pass = False

    if not res.get("converged", False):
        print(f"FAIL: Model did not converge (val_f1={f1:.4f} < 0.30)")
        all_pass = False

    if all_pass:
        print("PASS")
    return all_pass


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
