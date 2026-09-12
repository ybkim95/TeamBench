"""Class weighting utilities — contains inverted class weight bug."""
import numpy as np


N_CLASSES = 4
N_FEATURES = 20

# Class distribution fractions (for dataset generation)
CLASS_FRACS = np.array([0.50, 0.30, 0.15, 0.05], dtype=np.float64)


def make_imbalanced_dataset(n: int = 868, seed: int = 42) -> tuple:
    """
    Generate a imbalanced multiclass classification with rare categories.

    Class distribution: [0.50, 0.30, 0.15, 0.05]
    The minority class (class 3) has only ~{int(CLASS_FRACS[-1] * n)} samples.
    """
    rng = np.random.RandomState(seed)
    X_list, y_list = [], []
    for cls_id, frac in enumerate(CLASS_FRACS):
        n_cls = int(n * frac)
        # Each class has a different mean to make it separable
        mean = np.zeros(20)
        mean[cls_id % 20] = 2.0 * (cls_id + 1)
        X_cls = rng.randn(n_cls, 20).astype(np.float32) + mean
        y_cls = np.full(n_cls, cls_id, dtype=np.int64)
        X_list.append(X_cls)
        y_list.append(y_cls)
    X = np.vstack(X_list)
    y = np.concatenate(y_list)
    # Shuffle
    idx = rng.permutation(len(X))
    return X[idx], y[idx]


def compute_class_weights(y: np.ndarray, n_classes: int = N_CLASSES) -> np.ndarray:
    """
    Compute per-class weights for use in weighted cross-entropy loss.

    BUG: Weights are proportional to class FREQUENCY.
    This means common (majority) classes get HIGH weights, amplifying bias.

    The standard approach for imbalanced datasets is INVERSE frequency weighting:
    rarer classes should get higher weights to compensate for their low count.

    Returns: np.ndarray of shape (n_classes,) with per-class weights
    """
    counts = np.bincount(y, minlength=n_classes).astype(np.float64)

    # BUG: weights = frequency (majority class gets highest weight)
    weights = counts / (counts.sum() + 1e-8)  # BUG: proportional to count

    return weights.astype(np.float32)


def compute_minority_recall(y_true: np.ndarray, y_pred: np.ndarray,
                             minority_class: int = None) -> float:
    """Compute recall for the minority (last) class."""
    if minority_class is None:
        minority_class = len(np.unique(y_true)) - 1
    mask = y_true == minority_class
    if mask.sum() == 0:
        return 0.0
    return (y_pred[mask] == minority_class).mean()
