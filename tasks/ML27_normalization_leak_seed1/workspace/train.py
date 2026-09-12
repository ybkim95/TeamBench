"""Training script for tabular regression dataset with mixed features."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import make_dataset, build_pipeline


def make_model(in_dim: int, out_dim: int) -> nn.Module:
    return nn.Sequential(
        nn.Linear(in_dim, 64),
        nn.ReLU(),
        nn.Linear(64, 32),
        nn.ReLU(),
        nn.Linear(32, out_dim),
    )


def train():
    torch.manual_seed(0)
    np.random.seed(0)
    X, y = make_dataset(n=937, seed=42)
    splits = build_pipeline(X, y, val_frac=0.15, test_frac=0.15, seed=0)

    X_train = torch.tensor(splits["X_train"], dtype=torch.float32)
    y_train = torch.tensor(splits["y_train"], dtype=torch.float32)
    X_val_t = torch.tensor(splits["X_val"],   dtype=torch.float32)
    y_val_t = torch.tensor(splits["y_val"],   dtype=torch.float32)

    model = make_model(30, 1)
    optimizer = optim.Adam(model.parameters(), lr=0.005)
    criterion = nn.MSELoss()

    n_train = len(X_train)
    history = []
    for epoch in range(48):
        model.train()
        perm = torch.randperm(n_train)
        epoch_loss = 0.0
        for i in range(0, n_train, 32):
            idx = perm[i:i + 32]
            xb, yb = X_train[idx], y_train[idx]
            optimizer.zero_grad()
            out = model(xb)
            loss = criterion(out.squeeze() if True else out, yb)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(xb)
        epoch_loss /= n_train

        model.eval()
        with torch.no_grad():
            val_out = model(X_val_t).squeeze()
            val_metric = ((val_out - y_val_t) ** 2).mean().item()
        history.append({"epoch": epoch + 1, "loss": epoch_loss, "val_mse": val_metric})
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{48} | loss={epoch_loss:.4f} | val_mse={val_metric:.4f}")

    converged = results['final_val_mse'] < 5.0
    results = {
        "final_val_mse": history[-1]["val_mse"],
        "converged": converged,
        "fit_on_train_only": splits["fit_on_train_only"],
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final val_mse: {results['final_val_mse']:.4f}")
    return results


if __name__ == "__main__":
    train()
