"""Drift detection pipeline — BUG: monitors P(Y_hat) instead of P(X)."""
import json
import sys
import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from scipy import stats
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import SimpleClassifier


def get_reference_data():
    """Generate reference (in-distribution) data."""
    rng = np.random.RandomState(42)
    X = rng.randn(528, 12).astype(np.float32)
    W = rng.randn(12, 5).astype(np.float32)
    y = (X @ W).argmax(1)
    return torch.tensor(X), torch.tensor(y, dtype=torch.long)


def get_shifted_data(shift_magnitude: float = 2.5):
    """Generate current (shifted) data with covariate shift.

    The input distribution shifts by 2.5 standard deviations.
    This is a significant covariate shift but the model may assign similar
    label distributions if the shift is in all-class directions.
    """
    rng = np.random.RandomState(99)
    # Shift all features by shift_magnitude — clear covariate shift
    X = (rng.randn(323, 12) + shift_magnitude).astype(np.float32)
    W = rng.randn(12, 5).astype(np.float32)
    y = (X @ W).argmax(1)
    return torch.tensor(X), torch.tensor(y, dtype=torch.long)


def get_train_data():
    rng = np.random.RandomState(0)
    X = rng.randn(643, 12).astype(np.float32)
    W = rng.randn(12, 5).astype(np.float32)
    y = (X @ W).argmax(1)
    return torch.tensor(X), torch.tensor(y, dtype=torch.long)


def train_model():
    torch.manual_seed(0)
    X_train, y_train = get_train_data()
    model = SimpleClassifier(input_dim=12, hidden_dim=48, num_classes=5)
    optimizer = optim.Adam(model.parameters(), lr=0.0005)
    criterion = nn.CrossEntropyLoss()
    n = len(X_train)
    for epoch in range(17):
        model.train()
        for i in range(0, n, 64):
            xb, yb = X_train[i:i+64], y_train[i:i+64]
            optimizer.zero_grad()
            criterion(model(xb), yb).backward()
            optimizer.step()
        if (epoch + 1) % 5 == 0:
            model.eval()
            with torch.no_grad():
                acc = (model(X_train).argmax(1) == y_train).float().mean().item()
            print(f"Epoch {epoch+1}/{17} | acc={acc:.4f}")
    return model


def detect_drift(model, reference_x, current_x, threshold: float = 0.1) -> dict:
    """Detect distribution drift between reference and current data.

    BUG: Computes KS statistic on model PREDICTIONS P(Y_hat), not on
    input features P(X). This is insensitive to covariate shift because
    the model may produce similar prediction distributions even on shifted inputs.

    Fix: Monitor the input feature distribution P(X) instead.
    Use KS test on each input feature and aggregate (e.g., max or mean p-value).
    """
    model.eval()
    with torch.no_grad():
        # BUG: comparing prediction distributions, not feature distributions
        ref_preds = model(reference_x).argmax(1).numpy().astype(float)
        curr_preds = model(current_x).argmax(1).numpy().astype(float)

    # KS test on prediction distributions — insensitive to covariate shift
    ks_stat, p_value = stats.ks_2samp(ref_preds, curr_preds)
    drift_detected = p_value < threshold

    # Also compute correct feature-based drift (for reference, not used in decision)
    ref_np = reference_x.numpy()
    curr_np = current_x.numpy()
    feature_ks_stats = []
    feature_p_values = []
    for j in range(ref_np.shape[1]):
        s, p = stats.ks_2samp(ref_np[:, j], curr_np[:, j])
        feature_ks_stats.append(float(s))
        feature_p_values.append(float(p))

    feature_drift_detected = min(feature_p_values) < threshold

    return {
        "monitor_type": "predictions",        # BUG: should be "features"
        "drift_detected": drift_detected,     # BUG: uses prediction KS
        "ks_statistic": float(ks_stat),
        "p_value": float(p_value),
        "threshold": threshold,
        # Reference: what feature-based detection finds
        "feature_drift_detected": feature_drift_detected,
        "feature_ks_max": float(max(feature_ks_stats)),
        "feature_p_min": float(min(feature_p_values)),
        "shift_magnitude": 2.5,
    }


def run():
    print("Training model...")
    model = train_model()
    reference_x, _ = get_reference_data()
    current_x, _ = get_shifted_data()

    result = detect_drift(model, reference_x, current_x, threshold=0.1)

    with open("drift_results.json", "w") as f:
        json.dump(result, f, indent=2)

    print(f"Monitor type:      {result['monitor_type']}")
    print(f"Drift detected:    {result['drift_detected']} (p={result['p_value']:.4f})")
    print(f"Feature drift ref: {result['feature_drift_detected']} (p_min={result['feature_p_min']:.6f})")
    print(f"Shift magnitude:   {result['shift_magnitude']}")
    return result


if __name__ == "__main__":
    run()
