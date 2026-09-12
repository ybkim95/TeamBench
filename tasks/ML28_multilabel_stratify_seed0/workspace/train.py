"""Training script for multi-label multi-label text tagging dataset."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from splitter import make_multilabel_dataset, stratified_split


def make_model(in_dim: int, n_labels: int) -> nn.Module:
    return nn.Sequential(
        nn.Linear(in_dim, 64),
        nn.ReLU(),
        nn.Linear(64, 32),
        nn.ReLU(),
        nn.Linear(32, n_labels),
    )


def train():
    torch.manual_seed(0)
    np.random.seed(0)
    X, y = make_multilabel_dataset(n=797, seed=42)
    splits = stratified_split(X, y, val_frac=0.2, seed=0)

    X_train = torch.tensor(splits["X_train"], dtype=torch.float32)
    y_train = torch.tensor(splits["y_train"], dtype=torch.float32)
    X_val_t = torch.tensor(splits["X_val"],   dtype=torch.float32)
    y_val_t = torch.tensor(splits["y_val"],   dtype=torch.float32)

    model = make_model(16, 4)
    optimizer = optim.Adam(model.parameters(), lr=0.002)
    criterion = nn.BCEWithLogitsLoss()

    n_train = len(X_train)
    history = []
    for epoch in range(33):
        model.train()
        perm = torch.randperm(n_train)
        epoch_loss = 0.0
        for i in range(0, n_train, 32):
            idx = perm[i:i + 32]
            xb, yb = X_train[idx], y_train[idx]
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(xb)
        epoch_loss /= n_train

        model.eval()
        with torch.no_grad():
            val_logits = model(X_val_t)
            val_preds = (val_logits.sigmoid() > 0.5).float()
            val_f1 = (2 * (val_preds * y_val_t).sum() /
                      (val_preds.sum() + y_val_t.sum() + 1e-8)).item()

        history.append({"epoch": epoch + 1, "loss": epoch_loss, "val_f1": val_f1})
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{33} | loss={epoch_loss:.4f} | val_f1={val_f1:.4f}")

    results = {
        "final_val_f1": history[-1]["val_f1"],
        "converged": history[-1]["val_f1"] > 0.30,
        "stratify_all_labels": splits["stratify_all_labels"],
        "n_train": splits["n_train"],
        "n_val": splits["n_val"],
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final val F1: {results['final_val_f1']:.4f}")
    return results


if __name__ == "__main__":
    train()
