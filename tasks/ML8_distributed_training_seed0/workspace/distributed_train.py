"""Gradient accumulation training — contains 3 bugs."""
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.datasets import make_classification
import numpy as np
import json


ACCUMULATION_STEPS = 8
MICRO_BATCH_SIZE = 16
TOTAL_EPOCHS = 10


def get_data(seed=0):
    X, y = make_classification(n_samples=1864, n_features=28,
                                n_informative=10, random_state=seed)
    return (torch.tensor(X, dtype=torch.float32),
            torch.tensor(y, dtype=torch.long))


def get_model():
    return nn.Sequential(
        nn.Linear(28, 64), nn.ReLU(), nn.Dropout(0.3),
        nn.Linear(64, 32), nn.ReLU(),
        nn.Linear(32, 2)
    )


def train():
    torch.manual_seed(0)
    X, y = get_data()
    model = get_model()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()

    n = len(X)
    history = []

    for epoch in range(TOTAL_EPOCHS):
        model.train()
        total_loss = 0.0
        n_batches = 0

        for start in range(0, n, MICRO_BATCH_SIZE * ACCUMULATION_STEPS):
            # BUG 1: zero_grad called inside the accumulation loop
            # BUG 2: loss not scaled by ACCUMULATION_STEPS
            # BUG 3: optimizer.step() called every micro-batch

            for step in range(ACCUMULATION_STEPS):
                micro_start = start + step * MICRO_BATCH_SIZE
                micro_end = min(micro_start + MICRO_BATCH_SIZE, n)
                if micro_start >= n:
                    break

                xb = X[micro_start:micro_end]
                yb = y[micro_start:micro_end]

                optimizer.zero_grad()  # BUG 1: should be BEFORE this inner loop

                out = model(xb)
                loss = criterion(out, yb)
                # BUG 2: should divide by ACCUMULATION_STEPS
                loss.backward()

                optimizer.step()  # BUG 3: should only step after full accumulation
                total_loss += loss.item()
                n_batches += 1

        avg_loss = total_loss / max(n_batches, 1)
        history.append({"epoch": epoch + 1, "loss": avg_loss})
        if (epoch + 1) % 2 == 0:
            print(f"Epoch {epoch+1}: loss={avg_loss:.4f}")

    results = {
        "history": history,
        "final_loss": history[-1]["loss"],
        "converged": history[-1]["loss"] < history[0]["loss"] * 0.5,
        "accumulation_steps": ACCUMULATION_STEPS,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    return results


if __name__ == "__main__":
    train()
