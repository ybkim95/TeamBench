"""Training script for image classification with augmentation."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from augment import train_transform, val_transform, get_pipeline_order


def make_dataset(n: int = 428, seed: int = 42):
    """Generate synthetic grayscale medical image classification dataset."""
    rng = np.random.RandomState(seed)
    # Images in [0, 1]
    X = rng.rand(n, 1, 24, 24).astype(np.float32)
    # Labels based on mean intensity of each channel region
    y = (X[:, 0, :8, :8].mean(axis=(1, 2)) * 3).astype(np.int64).clip(0, 2)
    return X, y


class TinyConvNet(nn.Module):
    def __init__(self, n_channels: int, n_classes: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(n_channels, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.AdaptiveAvgPool2d(4),
            nn.Flatten(),
            nn.Linear(32 * 4 * 4, 64), nn.ReLU(),
            nn.Linear(64, n_classes),
        )

    def forward(self, x):
        return self.net(x)


def apply_augment(X_raw: np.ndarray, augment_fn, seed: int = 0) -> np.ndarray:
    rng = np.random.RandomState(seed)
    return np.stack([augment_fn(img, rng=rng) for img in X_raw])


def train():
    torch.manual_seed(0)
    np.random.seed(0)
    X_raw, y_all = make_dataset(n=428, seed=42)

    n = len(X_raw)
    n_train = int(n * 0.8)
    idx = np.random.RandomState(0).permutation(n)

    X_tr_raw = X_raw[idx[:n_train]]
    y_tr = y_all[idx[:n_train]]
    X_v_raw = X_raw[idx[n_train:]]
    y_v = y_all[idx[n_train:]]

    X_train = apply_augment(X_tr_raw, train_transform, seed=42)
    X_val   = apply_augment(X_v_raw, val_transform, seed=0)

    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_tr, dtype=torch.long)
    X_val_t   = torch.tensor(X_val,   dtype=torch.float32)
    y_val_t   = torch.tensor(y_v,     dtype=torch.long)

    model = TinyConvNet(n_channels=1, n_classes=3)
    optimizer = optim.Adam(model.parameters(), lr=0.0005)
    criterion = nn.CrossEntropyLoss()

    history = []
    n_train_samples = len(X_train_t)
    for epoch in range(16):
        model.train()
        perm = torch.randperm(n_train_samples)
        epoch_loss = 0.0
        for i in range(0, n_train_samples, 16):
            idx_b = perm[i:i + 16]
            optimizer.zero_grad()
            loss = criterion(model(X_train_t[idx_b]), y_train_t[idx_b])
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(idx_b)
        epoch_loss /= n_train_samples

        model.eval()
        with torch.no_grad():
            val_acc = (model(X_val_t).argmax(1) == y_val_t).float().mean().item()

        history.append({"epoch": epoch + 1, "loss": epoch_loss, "val_acc": val_acc})
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}/{16} | loss={epoch_loss:.4f} | val_acc={val_acc:.4f}")

    pipeline_order = get_pipeline_order()
    results = {
        "final_val_acc": history[-1]["val_acc"],
        "converged": history[-1]["val_acc"] > 0.40,
        "pipeline_order": pipeline_order,
        "augment_before_normalize": pipeline_order.startswith("flip") or pipeline_order.startswith("crop"),
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final val acc: {results['final_val_acc']:.4f}, order: {pipeline_order}")
    return results


if __name__ == "__main__":
    train()
