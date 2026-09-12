"""Training script for position-sensitive sequence classifier."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from positional_encoding import SinusoidalPE


class PositionAwareClassifier(nn.Module):
    """Sequence classifier that relies on positional information."""

    def __init__(self):
        super().__init__()
        self.input_proj = nn.Linear(8, 64)
        self.pe = SinusoidalPE(embed_dim=64, max_len=64)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=64, nhead=4, dim_feedforward=128,
            batch_first=True, dropout=0.1
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=3)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.head = nn.Linear(64, 3)

    def forward(self, x):
        # x: (B, T, 8)
        x = self.input_proj(x)
        x = self.pe(x)
        x = self.encoder(x)
        x = self.pool(x.transpose(1, 2)).squeeze(-1)
        return self.head(x)


def get_data():
    torch.manual_seed(42)
    # Position-sensitive task: class determined by position of maximum in each feature
    X = torch.randn(528, 12, 8)
    # Class = argmax position within first 4 positions modulo num_classes
    pos_signal = X[:, :4, 0]
    y = pos_signal.argmax(dim=1) % 3
    n_train = int(528 * 0.8)
    return X[:n_train], y[:n_train], X[n_train:], y[n_train:]


def train():
    torch.manual_seed(0)
    X_train, y_train, X_val, y_val = get_data()
    model = PositionAwareClassifier()
    optimizer = optim.Adam(model.parameters(), lr=0.002)
    criterion = nn.CrossEntropyLoss()

    n_train = len(X_train)
    history = []
    for epoch in range(21):
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
            print(f"Epoch {epoch+1}/{21} | loss={epoch_loss:.4f} | val_acc={val_acc:.4f}")

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
