"""Training with curriculum learning."""
import json, sys, os
import torch
import torch.nn as nn
import torch.optim as optim
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from curriculum import compute_difficulty_scores, get_curriculum_subset, pacing_function


def build_model():
    return nn.Sequential(
        nn.Linear(32, 64),
        nn.ReLU(),
        nn.Linear(64, 64),
        nn.ReLU(),
        nn.Linear(64, 4),
    )


def get_data():
    torch.manual_seed(42)
    X = torch.randn(997, 32)
    centers = torch.randn(4, 32)
    dists = torch.cdist(X, centers)
    y = dists.argmin(dim=1)
    y_cls = y
    n_train = int(997 * 0.8)
    return X[:n_train], y[:n_train], X[n_train:], y[n_train:], y_cls[:n_train]


def train():
    torch.manual_seed(0)
    X_train, y_train, X_val, y_val, y_cls_train = get_data()

    # Compute difficulty scores using class labels
    difficulty = compute_difficulty_scores(X_train, y_cls_train)
    print(f"Difficulty stats: min={difficulty.min():.3f} max={difficulty.max():.3f} mean={difficulty.mean():.3f}")

    model = build_model()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()

    history = []
    pacing_trace = []
    for epoch in range(43):
        # Get curriculum subset for this epoch
        X_sub, y_sub, fraction = get_curriculum_subset(
            X_train, y_train, difficulty, epoch, 43, start_fraction=0.3
        )
        pacing_trace.append(fraction)

        model.train()
        epoch_loss = 0.0
        n_sub = len(X_sub)
        indices = torch.randperm(n_sub)
        for i in range(0, n_sub, 32):
            idx = indices[i:i + 32]
            xb, yb = X_sub[idx], y_sub[idx]
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(xb)
        epoch_loss /= max(n_sub, 1)

        model.eval()
        with torch.no_grad():
            logits = model(X_val)
            val_metric = (logits.argmax(1) == y_val).float().mean().item()
        history.append({
            "epoch": epoch+1,
            "loss": epoch_loss,
            "val_metric": val_metric,
            "data_fraction": fraction,
            "n_samples_used": n_sub,
        })
        if (epoch+1) % 10 == 0:
            print(f"Epoch {epoch+1}/{43} loss={epoch_loss:.4f} val={val_metric:.4f} fraction={fraction:.3f}")

    results = {
        "final_val_metric": history[-1]["val_metric"],
        "converged": history[-1]["val_metric"] > 0.65,
        "pacing_start": pacing_trace[0],
        "pacing_end": pacing_trace[-1],
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final val metric: {results['final_val_metric']:.4f}")
    print(f"Pacing: start={pacing_trace[0]:.3f} end={pacing_trace[-1]:.3f}")
    return results


if __name__ == "__main__":
    train()
