"""Training script for image classification dataset with relabeled v2.1."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataset import (make_features, load_train_labels, load_eval_labels,
                     get_label_versions_match, count_label_mismatches)


def make_model(in_dim: int, n_classes: int) -> nn.Module:
    return nn.Sequential(
        nn.Linear(in_dim, 64), nn.ReLU(),
        nn.Linear(64, 32), nn.ReLU(),
        nn.Linear(32, n_classes),
    )


def train():
    torch.manual_seed(0)
    np.random.seed(0)

    X = make_features(n=797, seed=42)
    y_train_labels = load_train_labels(n=797, seed=42)  # v2.1
    y_eval_labels  = load_eval_labels(n=797, seed=42)   # BUG: v2.0

    n = len(X)
    n_train = int(n * 0.8)
    idx = np.random.RandomState(0).permutation(n)
    X_tr  = X[idx[:n_train]]
    y_tr  = y_train_labels[idx[:n_train]]
    X_v   = X[idx[n_train:]]
    y_v   = y_eval_labels[idx[n_train:]]   # BUG: evaluated with v2.0 labels

    X_train_t = torch.tensor(X_tr, dtype=torch.float32)
    y_train_t = torch.tensor(y_tr, dtype=torch.long)
    X_val_t   = torch.tensor(X_v,  dtype=torch.float32)
    y_val_t   = torch.tensor(y_v,  dtype=torch.long)

    model = make_model(20, 4)
    optimizer = optim.Adam(model.parameters(), lr=0.002)
    criterion = nn.CrossEntropyLoss()

    history = []
    n_train_s = len(X_train_t)
    for epoch in range(33):
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
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}/{33} | loss={epoch_loss:.4f} | val_acc={val_acc:.4f}")

    mismatch = count_label_mismatches(n=200, seed=42)
    versions_match = get_label_versions_match()

    results = {
        "final_val_acc": history[-1]["val_acc"],
        "converged": history[-1]["val_acc"] > 0.50,
        "versions_match": versions_match,
        "label_mismatch_rate": mismatch["mismatch_rate"],
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final val acc: {results['final_val_acc']:.4f}, versions_match={versions_match}, "
          f"mismatch_rate={mismatch['mismatch_rate']:.3f}")
    return results


if __name__ == "__main__":
    train()
