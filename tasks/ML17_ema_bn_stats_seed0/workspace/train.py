"""Training with EMA model for inference."""
import json, sys, os
import torch
import torch.nn as nn
import torch.optim as optim
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import BNModel
from ema import ModelEMA


def get_data():
    torch.manual_seed(42)
    X = torch.randn(997, 32)
    centers = torch.randn(4, 32)
    dists = torch.cdist(X, centers)
    y = dists.argmin(dim=1)
    n_train = int(997 * 0.8)
    return X[:n_train], y[:n_train], X[n_train:], y[n_train:]


def evaluate(model, X_val, y_val):
    model.eval()
    with torch.no_grad():
        return (model(X_val).argmax(1) == y_val).float().mean().item()


def train():
    torch.manual_seed(0)
    X_train, y_train, X_val, y_val = get_data()

    model = BNModel(input_dim=32, hidden_dim=64, num_classes=4)
    ema = ModelEMA(model, decay=0.95)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()

    n_train = len(X_train)
    history = []
    for epoch in range(38):
        model.train()
        epoch_loss = 0.0
        indices = torch.randperm(n_train)
        for i in range(0, n_train, 32):
            idx = indices[i:i + 32]
            xb, yb = X_train[idx], y_train[idx]
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()
            ema.update(model)
            epoch_loss += loss.item() * len(xb)
        epoch_loss /= n_train

        train_acc = evaluate(model, X_val, y_val)
        ema_acc = evaluate(ema.ema_model, X_val, y_val)

        history.append({
            "epoch": epoch+1,
            "loss": epoch_loss,
            "train_model_acc": train_acc,
            "ema_model_acc": ema_acc,
        })
        if (epoch+1) % 5 == 0:
            print(f"Epoch {epoch+1}/{38} loss={epoch_loss:.4f} "
                  f"train_acc={train_acc:.4f} ema_acc={ema_acc:.4f}")

    final_ema_acc = history[-1]["ema_model_acc"]
    final_train_acc = history[-1]["train_model_acc"]
    results = {
        "final_ema_acc": final_ema_acc,
        "final_train_acc": final_train_acc,
        "converged": final_ema_acc > 0.65,
        "ema_close_to_train": abs(final_ema_acc - final_train_acc) < 0.10,
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final: train_acc={final_train_acc:.4f} ema_acc={final_ema_acc:.4f}")
    return results


if __name__ == "__main__":
    train()
