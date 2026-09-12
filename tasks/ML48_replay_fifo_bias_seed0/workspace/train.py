"""Train continual learning model with experience replay."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from replay_buffer import ReplayBuffer
from model import ContinualModel


def make_task_data(task_id: int, n_samples: int = 398,
                   input_dim: int = 20):
    """Generate data for a specific task."""
    torch.manual_seed(42 + task_id * 100)
    n_classes_task = 2
    offset = task_id * n_classes_task
    centers = torch.randn(n_classes_task, input_dim) * 2.0 + task_id * 3.0
    X_list, y_list = [], []
    per_class = n_samples // n_classes_task
    for c in range(n_classes_task):
        X_list.append(centers[c] + 0.5 * torch.randn(per_class, input_dim))
        y_list.append(torch.full((per_class,), offset + c, dtype=torch.long))
    X = torch.cat(X_list)
    y = torch.cat(y_list)
    perm = torch.randperm(len(X))
    return X[perm], y[perm]


def evaluate_task(model, task_id: int, criterion):
    X, y = make_task_data(task_id, n_samples=200)
    model.eval()
    with torch.no_grad():
        logits = model(X)
        acc = (logits.argmax(1) == y).float().mean().item()
    return acc


def train():
    torch.manual_seed(0)
    np.random.seed(0)

    model = ContinualModel()
    optimizer = optim.Adam(model.parameters(), lr=0.0005)
    criterion = nn.CrossEntropyLoss()
    buffer = ReplayBuffer(capacity=200)

    task_accuracies = {}
    history = []

    for task_id in range(5):
        X_task, y_task = make_task_data(task_id)
        n = len(X_task)

        for epoch in range(16):
            model.train()
            indices = torch.randperm(n)
            for i in range(0, n, 32):
                idx = indices[i:i + 32]
                xb, yb = X_task[idx], y_task[idx]

                optimizer.zero_grad()
                loss = criterion(model(xb), yb)

                # Replay
                rx, ry = buffer.sample(40)
                if rx is not None:
                    loss = loss + criterion(model(rx), ry)

                loss.backward()
                optimizer.step()

        # Add task data to replay buffer
        buffer.add(X_task, y_task)

        # Evaluate all tasks seen so far
        task_accs = {}
        for prev_task in range(task_id + 1):
            acc = evaluate_task(model, prev_task, criterion)
            task_accs[f"task_{prev_task}"] = acc

        task_accuracies[f"after_task_{task_id}"] = task_accs
        history.append({"task_id": task_id, "accs": task_accs})
        print(f"After task {task_id}: {task_accs}")

    # Compute average forgetting: accuracy on task 0 after training all tasks
    task0_initial = task_accuracies["after_task_0"].get("task_0", 0)
    task0_final = task_accuracies[f"after_task_{5-1}"].get("task_0", 0)
    forgetting = task0_initial - task0_final

    converged = forgetting < 0.3 and task0_final > 0.3
    results = {
        "task_accuracies": task_accuracies,
        "task0_initial_acc": task0_initial,
        "task0_final_acc": task0_final,
        "forgetting": forgetting,
        "converged": converged,
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Task0 initial={task0_initial:.3f} final={task0_final:.3f} forgetting={forgetting:.3f}")
    return results


if __name__ == "__main__":
    train()
