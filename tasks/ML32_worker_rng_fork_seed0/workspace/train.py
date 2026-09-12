"""Training script using DataLoader with worker RNG."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataloader import AugmentedDataset, make_dataset, make_dataloader, check_worker_diversity


def make_model(in_dim: int, n_classes: int) -> nn.Module:
    return nn.Sequential(
        nn.Linear(in_dim, 64), nn.ReLU(),
        nn.Linear(64, 32), nn.ReLU(),
        nn.Linear(32, n_classes),
    )


def train():
    torch.manual_seed(0)
    np.random.seed(0)
    X, y = make_dataset(n=697, seed=42)

    n = len(X)
    n_train = int(n * 0.8)
    idx = np.random.RandomState(0).permutation(n)

    train_ds = AugmentedDataset(X[idx[:n_train]], y[idx[:n_train]], augment=True)
    val_ds   = AugmentedDataset(X[idx[n_train:]], y[idx[n_train:]], augment=False)

    train_loader = make_dataloader(train_ds, batch_size=32, shuffle=True,
                                   num_workers=4)
    val_loader   = make_dataloader(val_ds,   batch_size=32, shuffle=False,
                                   num_workers=0)

    model = make_model(32, 4)
    optimizer = optim.Adam(model.parameters(), lr=0.002)
    criterion = nn.CrossEntropyLoss()

    history = []
    for epoch in range(16):
        model.train()
        epoch_loss = 0.0
        n_seen = 0
        for xb, yb in train_loader:
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(xb)
            n_seen += len(xb)
        epoch_loss /= max(n_seen, 1)

        model.eval()
        correct = total = 0
        with torch.no_grad():
            for xb, yb in val_loader:
                preds = model(xb).argmax(1)
                correct += (preds == yb).sum().item()
                total += len(yb)
        val_acc = correct / max(total, 1)

        history.append({"epoch": epoch + 1, "loss": epoch_loss, "val_acc": val_acc})
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}/{16} | loss={epoch_loss:.4f} | val_acc={val_acc:.4f}")

    # Check worker diversity
    diversity = check_worker_diversity(train_ds, num_workers=4)

    results = {
        "final_val_acc": history[-1]["val_acc"],
        "converged": history[-1]["val_acc"] > 0.40,
        "has_worker_init_fn": diversity["has_worker_init_fn"],
        "num_workers": diversity["num_workers"],
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final val acc: {results['final_val_acc']:.4f}, has_worker_init_fn={results['has_worker_init_fn']}")
    return results


if __name__ == "__main__":
    train()
