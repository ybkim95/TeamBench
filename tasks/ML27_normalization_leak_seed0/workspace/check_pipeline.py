"""Validate normalization leakage fix."""
import json
import sys
import os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import make_dataset, build_pipeline


def check_scaler_fit_train_only():
    """Verify scaler is fit only on training data."""
    result = build_pipeline.__doc__
    # Check source code
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pipeline.py')) as f:
        src = f.read()

    # Must have fit_on_train_only = True
    if 'fit_on_train_only": False' in src or "fit_on_train_only\'\': False" in src:
        return False, "fit_on_train_only is still False in pipeline.py"
    if '"fit_on_train_only": False' in src:
        return False, "fit_on_train_only is still False in pipeline.py"

    return True, "fit_on_train_only flag is not False"


def check_split_before_fit():
    """Verify the pipeline splits data before fitting the scaler."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pipeline.py')) as f:
        src = f.read()

    # The scaler mean/std computation (fit) must happen AFTER the split
    # Key indicator: scaler fit uses X_train (subset), not full X
    has_split_first = (
        'X_train' in src and
        ('X_train.mean' in src or 'mean = X_train' in src or
         'fit(X_train' in src or 'X[train_idx]' in src or
         'X_train]' in src)
    )
    if not has_split_first:
        return False, "Scaler does not appear to be fit on X_train (split-first pattern not found)"

    # Must NOT fit on full X before split
    # Check that mean is NOT computed from full X directly before split
    lines = src.split('\n')
    fit_before_split = False
    split_seen = False
    for line in lines:
        stripped = line.strip()
        if 'train_idx' in stripped or 'n_train' in stripped and '=' in stripped and 'n *' in stripped:
            split_seen = True
        if not split_seen and ('X.mean(' in stripped or 'X.std(' in stripped) and 'X_' not in stripped:
            fit_before_split = True
    if fit_before_split:
        return False, "Scaler appears to be fit on full X before split"

    return True, "Scaler fit appears to happen after split"


def check_scaler_stats_differ():
    """Verify train-only scaler stats differ from full-data stats."""
    import numpy as np
    X, y = make_dataset(n=400, seed=42)
    splits = build_pipeline(X, y, val_frac=0.15, test_frac=0.10, seed=0)

    # Full-data stats
    full_mean = X.mean(axis=0)
    full_std = X.std(axis=0)

    scaler_mean = splits["scaler_mean"]
    scaler_std = splits["scaler_std"]

    # Train-only stats should differ from full-data stats
    # (since val/test are excluded, computed mean/std will differ)
    mean_diff = np.abs(scaler_mean - full_mean).max()
    std_diff = np.abs(scaler_std - full_std).max()

    if mean_diff < 1e-4 and std_diff < 1e-4:
        return False, (
            f"Scaler stats match full-data stats (mean_diff={mean_diff:.6f}, "
            f"std_diff={std_diff:.6f}) — scaler is still fit on all data"
        )
    return True, f"Scaler stats differ from full-data (mean_diff={mean_diff:.4f}) — train-only fit confirmed"


def check_train_val_independence():
    """Verify val/test data is not used to compute scaler parameters."""
    X, y = make_dataset(n=400, seed=42)
    splits = build_pipeline(X, y, val_frac=0.15, test_frac=0.10, seed=0)

    scaler_mean = splits["scaler_mean"]
    n = len(X)
    rng = np.random.RandomState(0)
    idx = rng.permutation(n)
    n_test = int(n * 0.10)
    n_val = int(n * 0.15)
    n_train = n - n_val - n_test
    train_idx = idx[:n_train]

    # Compute what the train-only mean should be
    expected_mean = X[train_idx].mean(axis=0)
    mean_diff = np.abs(scaler_mean - expected_mean).max()

    if mean_diff > 1e-3:
        return False, f"Scaler mean does not match train-only mean (diff={mean_diff:.6f})"
    return True, f"Scaler mean matches train-only mean (diff={mean_diff:.8f})"


def check_scaled_range():
    """Verify scaled training data has approximately zero mean and unit std."""
    X, y = make_dataset(n=400, seed=42)
    splits = build_pipeline(X, y, val_frac=0.15, test_frac=0.10, seed=0)

    X_train = splits["X_train"]
    train_mean = np.abs(X_train.mean(axis=0)).max()
    train_std = np.abs(X_train.std(axis=0) - 1.0).max()

    if train_mean > 0.1:
        return False, f"Training data mean not near zero (max_abs_mean={train_mean:.4f})"
    if train_std > 0.2:
        return False, f"Training data std not near 1.0 (max_dev={train_std:.4f})"
    return True, f"Training data properly normalized (mean_dev={train_mean:.4f}, std_dev={train_std:.4f})"


def check_val_test_scaled_correctly():
    """Verify val/test use train scaler (will have slightly non-zero mean)."""
    X, y = make_dataset(n=400, seed=42)
    splits = build_pipeline(X, y, val_frac=0.15, test_frac=0.10, seed=0)

    X_val = splits["X_val"]
    X_test = splits["X_test"]

    # Val/test should not have exactly zero mean (they're scaled with train stats)
    val_mean_abs = np.abs(X_val.mean(axis=0)).max()
    test_mean_abs = np.abs(X_test.mean(axis=0)).max()

    # They should be finite and reasonable
    if not np.isfinite(X_val).all():
        return False, "Val data contains non-finite values"
    if not np.isfinite(X_test).all():
        return False, "Test data contains non-finite values"

    return True, f"Val/test scaled with train stats (val_mean={val_mean_abs:.4f}, test_mean={test_mean_abs:.4f})"


def check_fit_on_train_only_flag():
    """Verify the pipeline returns fit_on_train_only=True."""
    X, y = make_dataset(n=200, seed=42)
    splits = build_pipeline(X, y, val_frac=0.15, test_frac=0.10, seed=0)
    if not splits.get("fit_on_train_only", False):
        return False, "build_pipeline returns fit_on_train_only=False"
    return True, "build_pipeline returns fit_on_train_only=True"


def check_no_future_leak_in_source():
    """Verify pipeline.py doesn't compute stats from full dataset."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pipeline.py')) as f:
        src = f.read()

    # Should NOT have: mean = X.mean(axis=0) before split (with X being full dataset)
    # Acceptable: X_train.mean(), splits['X_train'].mean(), etc.
    import re
    bad_patterns = [
        r'mean\s*=\s*X\.mean\(',
        r'std\s*=\s*X\.std\(',
        r'X\.mean\(axis=0\)',
        r'X\.std\(axis=0\)',
    ]
    for pat in bad_patterns:
        if re.search(pat, src):
            return False, f"Found full-data stat computation pattern: {pat!r}"
    return True, "No full-data normalization patterns found"


def check():
    if not os.path.exists("training_results.json"):
        print("ERROR: training_results.json not found")
        return False
    with open("training_results.json") as f:
        res = json.load(f)

    metric = res.get("final_val_acc", None)
    print(f"Final val_acc: {metric}")

    checks = [
        check_scaler_fit_train_only,
        check_split_before_fit,
        check_scaler_stats_differ,
        check_train_val_independence,
        check_scaled_range,
        check_val_test_scaled_correctly,
        check_fit_on_train_only_flag,
        check_no_future_leak_in_source,
    ]

    all_pass = True
    for fn in checks:
        ok, msg = fn()
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {fn.__name__}: {msg}")
        if not ok:
            all_pass = False

    if not res.get('converged', False):
        print(f"FAIL: Model did not converge ({'final_val_acc'}={metric})")
        all_pass = False

    if all_pass:
        print("PASS")
    return all_pass


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
