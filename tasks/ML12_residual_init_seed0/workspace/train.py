"""Training script for deep residual network for classification."""
import math
import json
import torch
import torch.nn as nn
import torch.optim as optim
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import ResNet, check_init_variance


def get_data():
    torch.manual_seed(42)
    X = torch.randn(997, 32)
    centers = torch.randn(4, 32)
    dists = torch.cdist(X, centers)
    y = dists.argmin(dim=1)
    n_train = int(997 * 0.8)
    return X[:n_train], y[:n_train], X[n_train:], y[n_train:]


def train():
    torch.manual_seed(0)
    X_train, y_train, X_val, y_val = get_data()
    model = ResNet(input_dim=32, hidden_dim=64,
                   num_classes=4, num_blocks=8)

    # Measure init variance before training
    init_stats = check_init_variance(model)
    print(f"Max init variance across blocks: {init_stats['max_variance']:.4f}")

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.0005)

    n_train = len(X_train)
    history = []
    for epoch in range(43):
        model.train()
        epoch_loss = 0.0
        indices = torch.randperm(n_train)
        for i in range(0, n_train, 32):
            idx = indices[i:i + 32]
            xb, yb = X_train[idx], y_train[idx]
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            epoch_loss += loss.item() * len(xb)
        epoch_loss /= n_train

        model.eval()
        with torch.no_grad():
            logits = model(X_val)
            val_metric = (logits.argmax(1) == y_val).float().mean().item()
        history.append({"epoch": epoch+1, "loss": epoch_loss, "val_metric": val_metric})
        if (epoch+1) % 10 == 0:
            print(f"Epoch {epoch+1}/{43} loss={epoch_loss:.4f} val={val_metric:.4f}")

    results = {
        "final_val_metric": history[-1]["val_metric"],
        "converged": history[-1]["val_metric"] > 0.65,
        "max_init_variance": init_stats["max_variance"],
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final metric: {results['final_val_metric']:.4f}")
    return results


if __name__ == "__main__":
    train()
