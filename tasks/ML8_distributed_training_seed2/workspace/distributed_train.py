"""AMP (automatic mixed precision) training — contains 3 bugs."""
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import json
from sklearn.datasets import make_classification


ACCUMULATION_STEPS = 4
MICRO_BATCH_SIZE = 16


def get_data(seed=2):
    X, y = make_classification(n_samples=1978, n_features=17,
                                n_informative=10, random_state=seed)
    return (torch.tensor(X, dtype=torch.float32),
            torch.tensor(y, dtype=torch.long))


def get_model():
    return nn.Sequential(
        nn.Linear(17, 64), nn.ReLU(), nn.Dropout(0.3),
        nn.Linear(64, 32), nn.ReLU(),
        nn.Linear(32, 2)
    )


def train():
    torch.manual_seed(2)
    X, y = get_data()
    model = get_model()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()
    scaler = torch.cuda.amp.GradScaler(enabled=False)  # enabled=False for CPU testing

    n = len(X)
    history = []

    for epoch in range(10):
        model.train()
        total_loss = 0.0
        n_batches = 0

        for start in range(0, n, MICRO_BATCH_SIZE):
            xb = X[start:start+MICRO_BATCH_SIZE]
            yb = y[start:start+MICRO_BATCH_SIZE]
            if len(xb) == 0:
                break

            optimizer.zero_grad()

            # BUG 1: autocast context missing — loss computed outside autocast
            out = model(xb)
            loss = criterion(out, yb)
            # Should be inside: with torch.cuda.amp.autocast():

            # BUG 2: gradient clipping before unscale
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)  # Wrong order
            # Should call scaler.unscale_(optimizer) FIRST, then clip

            scaled_loss = scaler.scale(loss)
            scaled_loss.backward()

            # BUG 3: scaler.update() missing
            scaler.step(optimizer)
            # Missing: scaler.update()

            total_loss += loss.item()
            n_batches += 1

        avg_loss = total_loss / max(n_batches, 1)
        history.append({"epoch": epoch+1, "loss": avg_loss})
        if (epoch+1) % 2 == 0:
            print(f"Epoch {epoch+1}: loss={avg_loss:.4f}")

    results = {
        "history": history,
        "final_loss": history[-1]["loss"],
        "converged": history[-1]["loss"] < history[0]["loss"] * 0.5,
        "amp_enabled": False,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    return results


if __name__ == "__main__":
    train()
