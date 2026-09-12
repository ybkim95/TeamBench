"""Multi-label dataset splitter — contains single-label stratification bug."""
import numpy as np


LABEL_NAMES = ['topic_A', 'topic_B', 'urgent', 'long_form']
N_LABELS = 4


def make_multilabel_dataset(n: int = 797, seed: int = 42) -> tuple:
    """
    Generate a multi-label text tagging dataset.

    Labels have correlated co-occurrence (e.g., label_0 and label_1 often appear together).
    Rare combinations exist (e.g., label_2=1, label_3=0, label_0=0 is rare).
    """
    rng = np.random.RandomState(seed)
    X = rng.randn(n, 16).astype(np.float32)

    # Generate correlated labels to create meaningful co-occurrence patterns
    base = rng.rand(n, 4)
    # Make some labels correlated
    base[:, 1] = 0.6 * base[:, 0] + 0.4 * rng.rand(n)
    # Make one label rare (~10% positive)
    base[:, -1] = rng.rand(n) * 0.3
    thresholds = [0.5] * 4
    thresholds[-1] = 0.1  # rare label
    y = np.column_stack([
        (base[:, i] > thresholds[i]).astype(np.int32)
        for i in range(4)
    ])
    return X, y


def stratified_split(X: np.ndarray, y: np.ndarray,
                     val_frac: float = 0.2,
                     seed: int = 0) -> dict:
    """
    Split multi-label dataset into train/val with stratification.

    BUG: Stratification uses only the first label (y[:, 0]).
    This ignores the joint distribution of all 4 labels.
    Rare co-occurrence patterns (e.g., label_0=1, label_3=1) will be
    unevenly distributed across splits.

    Correct: stratify by a composite key of all labels:
        label_keys = [''.join(map(str, row)) for row in y]
    """
    rng = np.random.RandomState(seed)
    n = len(X)
    idx = np.arange(n)

    # BUG: stratify by first label only — ignores co-occurrence of all 4 labels
    stratify_key = y[:, 0]  # BUG: should use composite key of ALL labels

    # Simple stratified split using single label
    n_val = int(n * val_frac)
    classes, counts = np.unique(stratify_key, return_counts=True)
    val_indices = []
    for cls, cnt in zip(classes, counts):
        cls_idx = idx[stratify_key == cls]
        rng.shuffle(cls_idx)
        n_cls_val = max(1, int(cnt * val_frac))
        val_indices.extend(cls_idx[:n_cls_val].tolist())

    val_set = set(val_indices)
    train_indices = [i for i in idx if i not in val_set]

    return {
        "X_train": X[train_indices],
        "y_train": y[train_indices],
        "X_val": X[val_indices],
        "y_val": y[val_indices],
        "stratify_all_labels": False,  # BUG: should be True
        "n_train": len(train_indices),
        "n_val": len(val_indices),
    }
