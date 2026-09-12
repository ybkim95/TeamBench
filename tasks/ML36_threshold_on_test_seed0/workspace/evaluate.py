"""Training and threshold evaluation pipeline.

BUG: The decision threshold is optimized by scanning over the TEST set,
then the same test set is used to report the final F1 score.
This is circular — the threshold is tuned to the test set.

Fix: Optimize threshold on VALIDATION set, evaluate on TEST set.
"""
import json
import sys
import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classifier import BinaryClassifier


def get_data():
    """Generate imbalanced binary classification dataset."""
    torch.manual_seed(42)
    rng = np.random.RandomState(42)
    n = 1194
    pos_frac = 0.15

    # Positive class: cluster around +1
    n_pos = int(n * pos_frac)
    n_neg = n - n_pos
    X_pos = torch.randn(n_pos, 20) + 0.8
    X_neg = torch.randn(n_neg, 20) - 0.3
    X = torch.cat([X_pos, X_neg])
    y = torch.cat([torch.ones(n_pos), torch.zeros(n_neg)])

    # Shuffle
    idx = torch.randperm(n)
    X, y = X[idx], y[idx]

    n_train = int(n * 0.6)
    n_val = int(n * 0.2)
    return (X[:n_train], y[:n_train],
            X[n_train:n_train+n_val], y[n_train:n_train+n_val],
            X[n_train+n_val:], y[n_train+n_val:])


def compute_f1(y_true, y_pred):
    """Compute binary F1 score."""
    tp = ((y_pred == 1) & (y_true == 1)).sum().item()
    fp = ((y_pred == 1) & (y_true == 0)).sum().item()
    fn = ((y_pred == 0) & (y_true == 1)).sum().item()
    if tp + fp == 0 or tp + fn == 0:
        return 0.0
    prec = tp / (tp + fp)
    rec = tp / (tp + fn)
    if prec + rec == 0:
        return 0.0
    return 2 * prec * rec / (prec + rec)


def find_best_threshold(probs, y_true):
    """Find threshold maximizing F1 on the given split."""
    best_t, best_f1 = 0.5, 0.0
    for t in np.arange(0.05, 0.95, 0.025):
        preds = (probs >= t).long()
        f1 = compute_f1(y_true, preds)
        if f1 > best_f1:
            best_f1, best_t = f1, t
    return best_t, best_f1


def train_model(X_train, y_train, X_val, y_val):
    torch.manual_seed(0)
    model = BinaryClassifier(input_dim=20, hidden_dim=64)
    pos_weight = torch.tensor([0.15 / (1 - 0.15)])
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = optim.Adam(model.parameters(), lr=0.002)

    n_train = len(X_train)
    for epoch in range(33):
        model.train()
        idx = torch.randperm(n_train)
        for i in range(0, n_train, 32):
            xb = X_train[idx[i:i+32]]
            yb = y_train[idx[i:i+32]]
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()
        if (epoch + 1) % 10 == 0:
            model.eval()
            with torch.no_grad():
                val_probs = model.predict_proba(X_val)
                _, val_f1_05 = 0.5, compute_f1(y_val, (val_probs >= 0.5).long())
            print(f"Epoch {epoch+1}/{33} | val_f1@0.5={val_f1_05:.4f}")
    return model


def evaluate():
    X_train, y_train, X_val, y_val, X_test, y_test = get_data()
    model = train_model(X_train, y_train, X_val, y_val)
    model.eval()

    with torch.no_grad():
        val_probs = model.predict_proba(X_val)
        test_probs = model.predict_proba(X_test)

    # BUG: threshold is found by scanning TEST set, not validation set
    # This is circular: we optimize threshold on test set then report test F1
    best_threshold, _ = find_best_threshold(test_probs, y_test)  # BUG: uses y_test

    # val_threshold, _ = find_best_threshold(val_probs, y_val)   # CORRECT

    test_preds = (test_probs >= best_threshold).long()
    reported_f1 = compute_f1(y_test, test_preds)

    # Also compute val threshold for comparison
    val_threshold, val_f1 = find_best_threshold(val_probs, y_val)
    honest_test_preds = (test_probs >= val_threshold).long()
    honest_f1 = compute_f1(y_test, honest_test_preds)

    results = {
        "reported_f1": reported_f1,
        "honest_f1": honest_f1,
        "best_threshold": float(best_threshold),
        "val_threshold": float(val_threshold),
        "threshold_source": "test_set",  # BUG: should be "val_set"
        "inflation": round(reported_f1 - honest_f1, 4),
    }
    with open("threshold_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Reported F1 (test-threshold): {reported_f1:.4f}")
    print(f"Honest F1   (val-threshold):  {honest_f1:.4f}")
    print(f"Inflation:  {results['inflation']:+.4f}")
    return results


if __name__ == "__main__":
    evaluate()
