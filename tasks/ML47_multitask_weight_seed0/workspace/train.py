"""Train multi-task model."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import MultiTaskModel
from trainer import MultiTaskTrainer


def make_data(n: int = 697, input_dim: int = 16, n_tasks: int = 2):
    torch.manual_seed(42)
    X = torch.randn(n, input_dim)
    # Tasks of different difficulties: easy (linear), hard (nonlinear)
    targets = []
    for i in range(n_tasks):
        w = torch.randn(input_dim)
        if i == 0:
            # Easy task: linear relationship
            y = X @ w / input_dim**0.5
        else:
            # Harder task: nonlinear + noise
            y = torch.sin(X @ w / input_dim**0.5) + 0.3 * torch.randn(n)
        targets.append(y)
    n_train = int(n * 0.8)
    X_train, X_val = X[:n_train], X[n_train:]
    targets_train = [t[:n_train] for t in targets]
    targets_val = [t[n_train:] for t in targets]
    return X_train, targets_train, X_val, targets_val


def train():
    torch.manual_seed(0)
    X_train, targets_train, X_val, targets_val = make_data()
    model = MultiTaskModel()
    trainer = MultiTaskTrainer()
    optimizer = optim.Adam(model.parameters(), lr=0.0005)
    criterion = nn.MSELoss()

    n = len(X_train)
    history = []
    crashed = False

    for epoch in range(133):
        model.train()
        indices = torch.randperm(n)
        epoch_losses = [0.0] * 2

        for i in range(0, n, 32):
            idx = indices[i:i + 32]
            xb = X_train[idx]
            preds = model(xb)
            task_losses = [criterion(preds[t], targets_train[t][idx]) for t in range(2)]

            try:
                total_loss = trainer.weighted_loss(task_losses)
                if not torch.isfinite(total_loss):
                    crashed = True
                    break
                optimizer.zero_grad()
                total_loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 10.0)
                optimizer.step()
            except Exception:
                crashed = True
                break

            for t in range(2):
                epoch_losses[t] += task_losses[t].item() * len(xb)

        if crashed:
            break

        for t in range(2):
            epoch_losses[t] /= n

        if (epoch + 1) % 20 == 0:
            model.eval()
            with torch.no_grad():
                val_preds = model(X_val)
                val_losses = [criterion(val_preds[t], targets_val[t]).item() for t in range(2)]
            history.append({
                "epoch": epoch + 1,
                "train_losses": epoch_losses,
                "val_losses": val_losses,
            })
            print(f"Epoch {epoch+1}/{133} train={epoch_losses} val={val_losses}")

    # Final evaluation
    model.eval()
    with torch.no_grad():
        val_preds = model(X_val)
        final_val_losses = [nn.MSELoss()(val_preds[t], targets_val[t]).item() for t in range(2)]

    converged = not crashed and all(l < 0.3 for l in final_val_losses)
    results = {
        "final_val_losses": final_val_losses,
        "converged": converged,
        "crashed": crashed,
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final val losses: {final_val_losses}, crashed={crashed}")
    return results


if __name__ == "__main__":
    train()
