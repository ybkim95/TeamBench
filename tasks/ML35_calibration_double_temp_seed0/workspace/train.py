"""Training script — trains model and saves calibration evaluation."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import CalibratedClassifier
from evaluator import ModelEvaluator


def get_data():
    torch.manual_seed(42)
    X = torch.randn(797, 64)
    # Multi-class labels based on linear combination of features
    W = torch.randn(64, 5)
    logits = X @ W
    y = logits.argmax(dim=1)
    n_train = int(797 * 0.7)
    n_val = int(797 * 0.15)
    return (X[:n_train], y[:n_train],
            X[n_train:n_train+n_val], y[n_train:n_train+n_val],
            X[n_train+n_val:], y[n_train+n_val:])


def train():
    torch.manual_seed(0)
    X_train, y_train, X_val, y_val, X_test, y_test = get_data()

    model = CalibratedClassifier(
        input_dim=64, hidden_dim=128,
        num_classes=5, temperature=1.8
    )
    optimizer = optim.Adam(model.parameters(), lr=0.002)
    criterion = nn.CrossEntropyLoss()

    n_train = len(X_train)
    for epoch in range(23):
        model.train()
        indices = torch.randperm(n_train)
        epoch_loss = 0.0
        for i in range(0, n_train, 32):
            idx = indices[i:i+32]
            xb, yb = X_train[idx], y_train[idx]
            optimizer.zero_grad()
            # Use raw logits for training (no temperature during training loss)
            raw_logits = model.get_raw_logits(xb)
            loss = criterion(raw_logits, yb)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(xb)
        epoch_loss /= n_train
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}/{23} | loss={epoch_loss:.4f}")

    evaluator = ModelEvaluator(model)

    val_acc = evaluator.compute_accuracy(X_val, y_val)
    val_ece = evaluator.compute_ece(X_val, y_val, n_bins=10)
    test_acc = evaluator.compute_accuracy(X_test, y_test)
    test_ece = evaluator.compute_ece(X_test, y_test, n_bins=10)

    results = {
        "val_accuracy": val_acc,
        "val_ece": val_ece,
        "test_accuracy": test_acc,
        "test_ece": test_ece,
        "temperature": 1.8,
        "calibration_ok": test_ece < 0.10,
    }
    with open("calibration_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Val acc: {val_acc:.4f}, Val ECE: {val_ece:.4f}")
    print(f"Test acc: {test_acc:.4f}, Test ECE: {test_ece:.4f}")
    print(f"Calibration OK: {results['calibration_ok']}")
    return results


if __name__ == "__main__":
    train()
