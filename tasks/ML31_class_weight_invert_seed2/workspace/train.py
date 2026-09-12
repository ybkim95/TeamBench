"""Training script for imbalanced classification."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from weighting import make_imbalanced_dataset, compute_class_weights, compute_minority_recall


def make_model(in_dim: int, n_classes: int) -> nn.Module:
    return nn.Sequential(
        nn.Linear(in_dim, 64), nn.ReLU(),
        nn.Linear(64, 32), nn.ReLU(),
        nn.Linear(32, n_classes),
    )


def train():
    torch.manual_seed(0)
    np.random.seed(0)
    X, y = make_imbalanced_dataset(n=828, seed=42)

    n = len(X)
    n_train = int(n * 0.8)
    idx = np.random.RandomState(0).permutation(n)
    X_tr, y_tr = X[idx[:n_train]], y[idx[:n_train]]
    X_v,  y_v  = X[idx[n_train:]], y[idx[n_train:]]

    # Compute class weights from training labels
    weights = compute_class_weights(y_tr, n_classes=3)
    weight_tensor = torch.tensor(weights, dtype=torch.float32)

    X_train_t = torch.tensor(X_tr, dtype=torch.float32)
    y_train_t = torch.tensor(y_tr, dtype=torch.long)
    X_val_t   = torch.tensor(X_v,  dtype=torch.float32)
    y_val_t   = torch.tensor(y_v,  dtype=torch.long)

    model = make_model(18, 3)
    optimizer = optim.Adam(model.parameters(), lr=0.005)
    criterion = nn.CrossEntropyLoss(weight=weight_tensor)

    history = []
    n_train_s = len(X_train_t)
    for epoch in range(32):
        model.train()
        perm = torch.randperm(n_train_s)
        epoch_loss = 0.0
        for i in range(0, n_train_s, 32):
            idx_b = perm[i:i + 32]
            optimizer.zero_grad()
            loss = criterion(model(X_train_t[idx_b]), y_train_t[idx_b])
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(idx_b)
        epoch_loss /= n_train_s

        model.eval()
        with torch.no_grad():
            val_logits = model(X_val_t)
            val_preds = val_logits.argmax(1).numpy()
            val_acc = (val_preds == y_v).mean()
            minority_recall = compute_minority_recall(y_v, val_preds)

        history.append({
            "epoch": epoch + 1,
            "loss": epoch_loss,
            "val_acc": float(val_acc),
            "minority_recall": float(minority_recall),
        })
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{32} | loss={epoch_loss:.4f} | "
                  f"val_acc={val_acc:.4f} | minority_recall={minority_recall:.4f}")

    final = history[-1]
    # Class weights diagnostic
    w_min_class = float(weights[-1])   # weight for minority class
    w_maj_class = float(weights[0])    # weight for majority class
    minority_upweighted = w_min_class > w_maj_class

    results = {
        "final_val_acc": final["val_acc"],
        "final_minority_recall": final["minority_recall"],
        "converged": final["minority_recall"] > 0.30,
        "minority_upweighted": minority_upweighted,
        "class_weights": weights.tolist(),
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final: val_acc={final['val_acc']:.4f}, minority_recall={final['minority_recall']:.4f}")
    print(f"Class weights: {weights.tolist()}, minority_upweighted={minority_upweighted}")
    return results


if __name__ == "__main__":
    train()
