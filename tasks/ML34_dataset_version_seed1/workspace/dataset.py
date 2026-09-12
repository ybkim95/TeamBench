"""Dataset loader with version mismatch bug."""
import numpy as np


N_CLASSES = 3
N_FEATURES = 16
RELABEL_FRAC = 0.2  # fraction of labels that differ between v2.0 and v2.1


def make_features(n: int = 668, seed: int = 42) -> np.ndarray:
    """Generate feature matrix for sentiment analysis dataset with annotation corrections."""
    rng = np.random.RandomState(seed)
    X = rng.randn(n, 16).astype(np.float32)
    return X


def make_labels_v2_0(n: int = 668, seed: int = 42) -> np.ndarray:
    """
    Generate v2.0 labels (original annotation, some contain errors).
    These are the initial crowd-sourced labels before quality review.
    """
    rng = np.random.RandomState(seed)
    X = make_features(n, seed)
    # True label: based on feature signal
    true_labels = (np.abs(X[:, :3].sum(axis=1)) % 3).astype(np.int64)
    # v2.0 has annotation errors: ~20% of labels are wrong
    error_mask = rng.rand(n) < 0.2
    noisy_labels = true_labels.copy()
    noisy_labels[error_mask] = (true_labels[error_mask] + rng.randint(1, 3, error_mask.sum())) % 3
    return noisy_labels


def make_labels_v2_1(n: int = 668, seed: int = 42) -> np.ndarray:
    """
    Generate v2.1 labels (corrected annotations after expert review).
    The ~20% of v2.0 errors have been fixed by domain experts.
    This is the ground truth used for training.
    """
    rng = np.random.RandomState(seed)
    X = make_features(n, seed)
    # v2.1: corrected labels (closer to true signal)
    true_labels = (np.abs(X[:, :3].sum(axis=1)) % 3).astype(np.int64)
    return true_labels


def load_train_labels(n: int = 668, seed: int = 42) -> np.ndarray:
    """Load training labels — uses v2.1 (correct, most recent)."""
    return make_labels_v2_1(n, seed)


def load_eval_labels(n: int = 668, seed: int = 42) -> np.ndarray:
    """
    Load evaluation labels.

    BUG: Returns v2.0 labels (original, with errors) instead of v2.1
    (corrected labels). Training uses v2.1 but evaluation uses v2.0.
    This creates a version mismatch: model is evaluated against stale labels.

    ~20% of evaluation samples have incorrect labels, making the
    model appear worse than it actually is on those examples.

    Correct: return make_labels_v2_1(n, seed) — same version as training.
    """
    # BUG: return stale v2.0 labels for evaluation
    return make_labels_v2_0(n, seed)  # BUG: should be make_labels_v2_1


def get_label_versions_match() -> bool:
    """Check whether train and eval use the same label version."""
    # BUG: currently False because load_eval_labels returns v2.0
    return False  # BUG: should be True after fix


def count_label_mismatches(n: int = 200, seed: int = 42) -> dict:
    """Diagnostic: count how many examples have different labels in v2.0 vs v2.1."""
    labels_v20 = make_labels_v2_0(n, seed)
    labels_v21 = make_labels_v2_1(n, seed)
    n_diff = (labels_v20 != labels_v21).sum()
    return {
        "n_total": n,
        "n_mismatched": int(n_diff),
        "mismatch_rate": float(n_diff) / n,
        "expected_mismatch_rate": RELABEL_FRAC,
    }
