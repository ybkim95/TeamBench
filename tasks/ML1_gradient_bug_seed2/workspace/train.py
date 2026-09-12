"""Training script for regression."""
import torch
import torch.nn as nn
import torch.optim as optim
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import MLP


def get_data():
    """Generate synthetic regression dataset."""
    torch.manual_seed(42)
    X = torch.randn(828, 32)
    w = torch.randn(32)
    y = (X @ w).unsqueeze(1) + 0.1 * torch.randn(828, 1)
    n_train = int(len(X) * 0.8)
    return X[:n_train], y[:n_train], X[n_train:], y[n_train:]


def evaluate(model, X_val, y_val):
    # Evaluate — BUG: model.train() should be model.eval()
    model.train()  # BUG: BatchNorm normalises using noisy batch stats during eval
    with torch.no_grad():
        preds  = model(X_val)
        ss_res = ((preds - y_val) ** 2).sum()
        ss_tot = ((y_val - y_val.mean()) ** 2).sum()
        r2     = 1 - ss_res / ss_tot
    return r2.item()


def train():
    torch.manual_seed(0)
    X_train, y_train, X_val, y_val = get_data()

    model = MLP(input_dim=32, output_dim=1)

    criterion = nn.CrossEntropyLoss()

    optimizer = optim.AdamW(model.parameters(), lr=10.0, weight_decay=0.1)

    scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(
        optimizer, T_0=3, T_mult=1
    )

    n_epochs   = 16
    batch_size = 32
    n_train    = len(X_train)

    history = []
    for epoch in range(n_epochs):
        model.train()
        epoch_loss = 0.0
        indices = torch.randperm(n_train)
        for i in range(0, n_train, batch_size):
            batch_idx = indices[i:i + batch_size]
            xb = X_train[batch_idx]
            yb = y_train[batch_idx]
            optimizer.zero_grad()
            out  = model(xb)
            loss = criterion(out, yb)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(xb)

        epoch_loss /= n_train
        scheduler.step()

        val_metric = evaluate(model, X_val, y_val)
        history.append({"epoch": epoch + 1, "loss": epoch_loss, "val_metric": val_metric})

        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}/16 | loss: {epoch_loss:.4f} | val: {val_metric:.4f}")

    final_metric = history[-1]["val_metric"]
    results = {
        "final_val_metric": final_metric,
        "converged": final_metric > 0.70,
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final val metric: {final_metric:.4f} | converged: {final_metric > 0.70}")
    return results


if __name__ == "__main__":
    train()
