"""Train BYOL and evaluate with linear probe."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from byol import BYOL


def augment(X, strength=0.1):
    return X + strength * torch.randn_like(X)


def get_data():
    torch.manual_seed(42)
    centers = torch.randn(4, 32) * 2.0
    X_list, y_list = [], []
    per_class = 797 // 4
    for c in range(4):
        X_list.append(centers[c] + 0.4 * torch.randn(per_class, 32))
        y_list.append(torch.full((per_class,), c, dtype=torch.long))
    X = torch.cat(X_list)
    y = torch.cat(y_list)
    perm = torch.randperm(len(X))
    X, y = X[perm], y[perm]
    n_train = int(len(X) * 0.8)
    return X[:n_train], y[:n_train], X[n_train:], y[n_train:]


def linear_probe(byol, X_train, y_train, X_val, y_val):
    h_train = byol.get_representation(X_train)
    h_val = byol.get_representation(X_val)
    probe = nn.Linear(128, 4)
    opt = optim.Adam(probe.parameters(), lr=1e-2)
    criterion = nn.CrossEntropyLoss()
    for _ in range(200):
        opt.zero_grad()
        loss = criterion(probe(h_train.detach()), y_train)
        loss.backward()
        opt.step()
    with torch.no_grad():
        acc = (probe(h_val).argmax(1) == y_val).float().mean().item()
    return acc


def train():
    torch.manual_seed(0)
    X_train, y_train, X_val, y_val = get_data()
    byol = BYOL()
    # Optimizer includes both online encoder and predictor
    params = list(byol.online.parameters()) + list(byol.predictor.parameters())
    optimizer = optim.Adam(params, lr=0.001)

    n = len(X_train)
    history = []
    for epoch in range(43):
        byol.online.train()
        indices = torch.randperm(n)
        losses = []
        for i in range(0, n, 32):
            idx = indices[i:i + 32]
            xb = X_train[idx]
            x1, x2 = augment(xb), augment(xb)
            loss_val = byol.update(x1, x2, optimizer)
            losses.append(loss_val)

        if (epoch + 1) % 10 == 0:
            acc = linear_probe(byol, X_train, y_train, X_val, y_val)
            history.append({"epoch": epoch + 1, "loss": sum(losses)/len(losses), "probe_acc": acc})
            print(f"Epoch {epoch+1}/{43} loss={sum(losses)/len(losses):.4f} probe_acc={acc:.4f}")

    final_acc = linear_probe(byol, X_train, y_train, X_val, y_val)
    results = {
        "final_probe_acc": final_acc,
        "converged": final_acc > 0.55,
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final probe acc: {final_acc:.4f}")
    return results


if __name__ == "__main__":
    train()
