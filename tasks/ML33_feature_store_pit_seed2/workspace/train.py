"""Training script for customer churn prediction with behavioral features."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from feature_store import (make_feature_store, make_label_events,
                           build_feature_matrix, check_pit_correctness)


def make_model(in_dim: int, n_classes: int) -> nn.Module:
    return nn.Sequential(
        nn.Linear(in_dim, 32), nn.ReLU(),
        nn.Linear(32, 16), nn.ReLU(),
        nn.Linear(16, n_classes),
    )


def train():
    torch.manual_seed(0)
    np.random.seed(0)

    feature_store = make_feature_store(n_entities=328, seed=42)
    events = make_label_events(feature_store, n_entities=328, seed=42)

    X, y = build_feature_matrix(events, feature_store)

    n = len(X)
    n_train = int(n * 0.8)
    idx = np.random.RandomState(0).permutation(n)
    X_tr, y_tr = X[idx[:n_train]], y[idx[:n_train]]
    X_v,  y_v  = X[idx[n_train:]], y[idx[n_train:]]

    X_train_t = torch.tensor(X_tr, dtype=torch.float32)
    y_train_t = torch.tensor(y_tr, dtype=torch.long)
    X_val_t   = torch.tensor(X_v,  dtype=torch.float32)
    y_val_t   = torch.tensor(y_v,  dtype=torch.long)

    model = make_model(4, 2)
    optimizer = optim.Adam(model.parameters(), lr=0.002)
    criterion = nn.CrossEntropyLoss()

    history = []
    n_train_s = len(X_train_t)
    for epoch in range(22):
        model.train()
        perm = torch.randperm(n_train_s)
        epoch_loss = 0.0
        for i in range(0, n_train_s, 32):
            idx_b = perm[i:i + 32]
            optimizer.zero_grad()
            loss = criterion(model(X_train_t[idx_b]), y_train_t[idx_b])
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(idx_b)
        epoch_loss /= n_train_s

        model.eval()
        with torch.no_grad():
            val_acc = (model(X_val_t).argmax(1) == y_val_t).float().mean().item()

        history.append({"epoch": epoch + 1, "loss": epoch_loss, "val_acc": val_acc})
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{22} | loss={epoch_loss:.4f} | val_acc={val_acc:.4f}")

    pit_check = check_pit_correctness()
    results = {
        "final_val_acc": history[-1]["val_acc"],
        "converged": history[-1]["val_acc"] > 0.45,
        "uses_strict_lt": pit_check["uses_strict_lt"],
        "pit_operator": pit_check["operator"],
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final val acc: {results['final_val_acc']:.4f}, PIT operator: {pit_check['operator']}")
    return results


if __name__ == "__main__":
    train()
