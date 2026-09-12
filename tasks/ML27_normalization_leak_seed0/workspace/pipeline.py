"""Data pipeline — contains normalization leakage bug."""
import numpy as np


def make_dataset(n: int = 1194, seed: int = 42) -> tuple:
    """Generate synthetic tabular binary classification dataset."""
    rng = np.random.RandomState(seed)
    # Features: mix of different scales to make normalization important
    X = rng.randn(n, 20).astype(np.float32)
    # Scale some features to very different ranges to highlight normalization effect
    X[:, 0] *= 100.0   # large scale feature
    X[:, 1] *= 0.01    # small scale feature
    X[:, 2] += 50.0    # shifted feature
    y = (np.abs(X[:, :3].sum(axis=1)) % 2).astype(np.int64)
    return X, y


def build_pipeline(X: np.ndarray, y: np.ndarray,
                   val_frac: float = 0.2,
                   test_frac: float = 0.15,
                   seed: int = 0) -> dict:
    """
    Build train/val/test splits with feature normalization.

    BUG: StandardScaler is fit on ALL data before splitting.
    This leaks val/test distribution information into the scaler parameters
    (mean and std), which are then used during training.

    Correct approach: fit scaler ONLY on training data, then transform val/test.
    """
    n = len(X)
    rng = np.random.RandomState(seed)
    idx = rng.permutation(n)
    n_test = int(n * test_frac)
    n_val = int(n * val_frac)
    n_train = n - n_val - n_test

    # BUG: Fit scaler on ALL data before splitting
    # Correct: split first, then fit scaler only on X_train
    mean = X.mean(axis=0)   # BUG: computed over full dataset
    std = X.std(axis=0) + 1e-8  # BUG: computed over full dataset

    X_scaled = (X - mean) / std  # BUG: scaled with full-data stats

    # Now split the already-contaminated scaled data
    train_idx = idx[:n_train]
    val_idx = idx[n_train:n_train + n_val]
    test_idx = idx[n_train + n_val:]

    return {
        "X_train": X_scaled[train_idx],
        "y_train": y[train_idx],
        "X_val": X_scaled[val_idx],
        "y_val": y[val_idx],
        "X_test": X_scaled[test_idx],
        "y_test": y[test_idx],
        "scaler_mean": mean,
        "scaler_std": std,
        "fit_on_train_only": False,  # BUG: this should be True
    }
