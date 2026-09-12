"""Training script for multi-head attention classifier."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from attention import MultiHeadAttention


class AttentionClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.input_proj = nn.Linear(8, 48)
        self.attn = MultiHeadAttention(embed_dim=48, num_heads=4)
        self.ff = nn.Sequential(
            nn.Linear(48, 96),
            nn.ReLU(),
            nn.Linear(96, 48),
        )
        self.norm1 = nn.LayerNorm(48)
        self.norm2 = nn.LayerNorm(48)
        self.head = nn.Linear(48, 5)

    def forward(self, x):
        x = self.input_proj(x)
        x = x + self.attn(self.norm1(x))
        x = x + self.ff(self.norm2(x))
        return self.head(x.mean(dim=1))


def get_data():
    torch.manual_seed(42)
    X = torch.randn(568, 20, 8)
    centers = torch.randn(5, 8)
    dists = torch.cdist(X.mean(1), centers)
    y = dists.argmin(dim=1)
    n_train = int(568 * 0.8)
    return X[:n_train], y[:n_train], X[n_train:], y[n_train:]


def train():
    torch.manual_seed(0)
    X_train, y_train, X_val, y_val = get_data()
    model = AttentionClassifier()
    optimizer = optim.Adam(model.parameters(), lr=0.002)
    criterion = nn.CrossEntropyLoss()

    n_train = len(X_train)
    history = []
    for epoch in range(29):
        model.train()
        epoch_loss = 0.0
        indices = torch.randperm(n_train)
        for i in range(0, n_train, 16):
            idx = indices[i:i + 16]
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
            val_acc = (model(X_val).argmax(1) == y_val).float().mean().item()

        history.append({"epoch": epoch + 1, "loss": epoch_loss, "val_acc": val_acc})
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}/{29} | loss={epoch_loss:.4f} | val_acc={val_acc:.4f}")

    results = {
        "final_val_acc": history[-1]["val_acc"],
        "converged": history[-1]["val_acc"] > 0.55,
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final val acc: {results['final_val_acc']:.4f}")
    return results


if __name__ == "__main__":
    train()
