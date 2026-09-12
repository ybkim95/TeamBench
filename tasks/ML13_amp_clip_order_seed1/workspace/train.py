"""Training with AMP — contains gradient clip order bug."""
import json, math, sys, os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.cuda.amp import GradScaler
import contextlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def build_model(input_dim, hidden_dim, num_classes):
    return nn.Sequential(
            nn.Linear(96, 192), nn.LayerNorm(192), nn.GELU(),
            nn.Linear(192, 192), nn.LayerNorm(192), nn.GELU(),
            nn.Linear(192, 192), nn.LayerNorm(192), nn.GELU(),
            nn.Linear(192, 192), nn.LayerNorm(192), nn.GELU(),
            nn.Linear(192, 4)
    )


def get_data():
    torch.manual_seed(42)
    X = torch.randn(868, 96)
    centers = torch.randn(4, 96)
    dists = torch.cdist(X, centers)
    y = dists.argmin(dim=1)
    n_train = int(868 * 0.8)
    return X[:n_train], y[:n_train], X[n_train:], y[n_train:]


def train():
    torch.manual_seed(0)
    device = torch.device("cpu")  # CPU for compatibility (AMP still simulated)
    X_train, y_train, X_val, y_val = get_data()
    X_train, y_train = X_train.to(device), y_train.to(device)
    X_val, y_val = X_val.to(device), y_val.to(device)

    model = build_model(96, 192, 4).to(device)
    optimizer = optim.Adam(model.parameters(), lr=0.002)
    criterion = nn.CrossEntropyLoss()

    # GradScaler — on CPU it won't actually scale but the order bug
    # still demonstrates the wrong pattern (and on GPU it would be critical)
    scaler = GradScaler(enabled=False)  # disabled for CPU, but order matters on GPU
    max_norm = 1.0

    n_train = len(X_train)
    history = []
    grad_norms_before_clip = []

    for epoch in range(29):
        model.train()
        epoch_loss = 0.0
        indices = torch.randperm(n_train)
        for i in range(0, n_train, 32):
            idx = indices[i:i + 32]
            xb, yb = X_train[idx], y_train[idx]

            optimizer.zero_grad()
            with contextlib.nullcontext():
                loss = criterion(model(xb), yb)

            scaler.scale(loss).backward()

            # BUG: Clipping BEFORE unscale — on GPU this clips scaled gradients
            # (scaled by scaler's scale factor ~2^16), so clip has no effect
            grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm)
            grad_norms_before_clip.append(grad_norm.item())

            # scaler.unscale_(optimizer)  # <-- should come BEFORE clip
            scaler.step(optimizer)
            scaler.update()
            epoch_loss += loss.item() * len(xb)

        epoch_loss /= n_train
        model.eval()
        with torch.no_grad():
            val_acc = (model(X_val).argmax(1) == y_val).float().mean().item()

        history.append({"epoch": epoch+1, "loss": epoch_loss, "val_acc": val_acc})
        if (epoch+1) % 5 == 0:
            avg_gnorm = sum(grad_norms_before_clip[-10:]) / min(10, len(grad_norms_before_clip))
            print(f"Epoch {epoch+1}/{29} loss={epoch_loss:.4f} val={val_acc:.4f} avg_gnorm={avg_gnorm:.4f}")

    results = {
        "final_val_acc": history[-1]["val_acc"],
        "converged": history[-1]["val_acc"] > 0.65,
        "history": history,
        "avg_grad_norm_last_epoch": sum(grad_norms_before_clip[-20:]) / max(1, min(20, len(grad_norms_before_clip))),
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final val acc: {results['final_val_acc']:.4f}")
    return results


if __name__ == "__main__":
    train()
