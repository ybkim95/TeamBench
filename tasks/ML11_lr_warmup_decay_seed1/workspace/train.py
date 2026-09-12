"""Training script for convolutional image classifier."""
import math
import json
import torch
import torch.nn as nn
import torch.optim as optim
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scheduler import WarmupCosineScheduler


def build_model():
    return nn.Sequential(
            nn.Linear(48, 96),
            nn.ReLU(),
            nn.LayerNorm(96),
            nn.Linear(96, 96),
            nn.ReLU(),
            nn.LayerNorm(96),
            nn.Linear(96, 96),
            nn.ReLU(),
            nn.LayerNorm(96),
            nn.Linear(96, 5),
    )


def get_data():
    torch.manual_seed(42)
    X = torch.randn(668, 48)
    centers = torch.randn(5, 48)
    dists = torch.cdist(X, centers)
    y = dists.argmin(dim=1)
    n_train = int(668 * 0.8)
    return X[:n_train], y[:n_train], X[n_train:], y[n_train:]


def train():
    torch.manual_seed(0)
    X_train, y_train, X_val, y_val = get_data()
    model = build_model()
    optimizer = optim.AdamW(model.parameters(), lr=0.002, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()

    n_train = len(X_train)
    steps_per_epoch = max(1, n_train // 32)
    total_steps = 29 * steps_per_epoch
    warmup_steps = int(total_steps * 0.1)

    scheduler = WarmupCosineScheduler(
        optimizer, base_lr=0.002,
        warmup_steps=warmup_steps,
        total_steps=total_steps
    )

    history = []
    lr_trace = []
    for epoch in range(29):
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
            scheduler.step()
            epoch_loss += loss.item() * len(xb)
            lr_trace.append(scheduler.get_last_lr())
        epoch_loss /= n_train

        model.eval()
        with torch.no_grad():
            val_logits = model(X_val)
            val_acc = (val_logits.argmax(1) == y_val).float().mean().item()

        history.append({"epoch": epoch + 1, "loss": epoch_loss, "val_acc": val_acc})
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}/{29} | loss={epoch_loss:.4f} | val_acc={val_acc:.4f} | lr={lr_trace[-1]:.6f}")

    results = {
        "final_val_acc": history[-1]["val_acc"],
        "converged": history[-1]["val_acc"] > 0.65,
        "history": history,
        "lr_at_warmup_end": lr_trace[warmup_steps] if warmup_steps < len(lr_trace) else None,
        "lr_at_start": lr_trace[0] if lr_trace else None,
        "lr_at_end": lr_trace[-1] if lr_trace else None,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final val acc: {results['final_val_acc']:.4f}")
    return results


if __name__ == "__main__":
    train()
