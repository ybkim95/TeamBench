"""Training script for residual network for regression."""
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
    X = torch.randn(868, 24)
    w = torch.randn(24) / math.sqrt(24)
    y = (X @ w).unsqueeze(1) + 0.1 * torch.randn(868, 1)
    n_train = int(868 * 0.8)
    return X[:n_train], y[:n_train], X[n_train:], y[n_train:]


def train():
    torch.manual_seed(0)
    X_train, y_train, X_val, y_val = get_data()
    model = ResNet(input_dim=24, hidden_dim=48,
                   num_classes=1, num_blocks=10)

    # Measure init variance before training
    init_stats = check_init_variance(model)
    print(f"Max init variance across blocks: {init_stats['max_variance']:.4f}")

    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.0005)

    n_train = len(X_train)
    history = []
    for epoch in range(48):
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
            preds = model(X_val)
            ss_res = ((preds - y_val) ** 2).sum()
            ss_tot = ((y_val - y_val.mean()) ** 2).sum()
            val_metric = (1 - ss_res / ss_tot).item()
        history.append({"epoch": epoch+1, "loss": epoch_loss, "val_metric": val_metric})
        if (epoch+1) % 10 == 0:
            print(f"Epoch {epoch+1}/{48} loss={epoch_loss:.4f} val={val_metric:.4f}")

    results = {
        "final_val_metric": history[-1]["val_metric"],
        "converged": history[-1]["val_metric"] > 0.5,
        "max_init_variance": init_stats["max_variance"],
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final metric: {results['final_val_metric']:.4f}")
    return results


if __name__ == "__main__":
    train()
