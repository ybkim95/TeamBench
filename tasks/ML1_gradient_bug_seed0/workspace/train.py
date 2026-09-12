"""Training script for binary_classification."""
import torch
import torch.nn as nn
import torch.optim as optim
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import MLP


def get_data():
    """Generate synthetic binary_classification dataset."""
    torch.manual_seed(42)
    X = torch.randn(997, 16)
    w = torch.randn(16)
    y = (X @ w > 0).float().unsqueeze(1)
    n_train = int(len(X) * 0.8)
    return X[:n_train], y[:n_train], X[n_train:], y[n_train:]


def evaluate(model, X_val, y_val):
    # Evaluate — BUG: model.train() should be model.eval()
    model.train()  # BUG: keeps BatchNorm in training mode, uses noisy batch stats
    with torch.no_grad():
        logits = model(X_val)
        preds  = (logits > 0).float()
        acc    = (preds == y_val).float().mean().item()
    return acc


def train():
    torch.manual_seed(0)
    X_train, y_train, X_val, y_val = get_data()

    model = MLP(input_dim=16, output_dim=1)

    criterion = nn.MSELoss()

    optimizer = optim.AdamW(model.parameters(), lr=1.0, weight_decay=0.1)

    scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(
        optimizer, T_0=4, T_mult=1
    )

    n_epochs   = 21
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
            print(f"Epoch {epoch+1}/21 | loss: {epoch_loss:.4f} | val: {val_metric:.4f}")

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
