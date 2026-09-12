"""Simulated DDP training (single-process simulation) — contains 3 bugs."""
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import json
from sklearn.datasets import make_classification


# Simulated multi-process scenario (single process for testing)
WORLD_SIZE = 2
ACCUMULATION_STEPS = 8
MICRO_BATCH_SIZE = 16


def get_data(seed=1):
    X, y = make_classification(n_samples=1137, n_features=18,
                                n_informative=10, random_state=seed)
    return (torch.tensor(X, dtype=torch.float32),
            torch.tensor(y, dtype=torch.long))


def simulate_allreduce(params):
    """Simulate gradient all-reduce (average across workers)."""
    # In real DDP, this averages gradients across all ranks
    for p in params:
        if p.grad is not None:
            p.grad.data /= WORLD_SIZE


def get_model():
    return nn.Sequential(
        nn.Linear(18, 64), nn.ReLU(), nn.Dropout(0.3),
        nn.Linear(64, 32), nn.ReLU(),
        nn.Linear(32, 2)
    )


def train():
    torch.manual_seed(1)
    X, y = get_data()
    model = get_model()
    optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.9)
    criterion = nn.CrossEntropyLoss()

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

            # BUG 1: all-reduce BEFORE backward (operates on zero/stale gradients)
            simulate_allreduce(list(model.parameters()))  # Should be AFTER backward

            optimizer.zero_grad()
            out = model(xb)
            loss = criterion(out, yb)
            loss.backward()
            # Correct place for all-reduce would be here

            optimizer.step()
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
        "world_size": WORLD_SIZE,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    return results


if __name__ == "__main__":
    train()
