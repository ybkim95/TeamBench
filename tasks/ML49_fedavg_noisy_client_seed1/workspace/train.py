"""Federated learning training simulation."""
import json
import sys
import os
import torch
import torch.nn as nn
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fedavg import ClientModel, FedAvgClient, FedAvgServer


def make_client_data(client_id: int, n_samples: int, is_noisy: bool = False):
    torch.manual_seed(42 + client_id * 17)
    centers = torch.randn(5, 20)
    X_list, y_list = [], []
    per_class = n_samples // 5
    for c in range(5):
        X_list.append(centers[c] + 0.5 * torch.randn(per_class, 20))
        y_list.append(torch.full((per_class,), c, dtype=torch.long))
    X = torch.cat(X_list)
    y = torch.cat(y_list)
    if is_noisy:
        # Noisy client: add large noise and randomly shuffle labels
        X = X + 3.0 * torch.randn_like(X)
        y = torch.randint(0, 5, (len(y),))
    return X, y


def evaluate(model, n_eval: int = 300):
    torch.manual_seed(999)
    centers = torch.randn(5, 20)
    X_list, y_list = [], []
    per_class = n_eval // 5
    for c in range(5):
        X_list.append(centers[c] + 0.5 * torch.randn(per_class, 20))
        y_list.append(torch.full((per_class,), c, dtype=torch.long))
    X = torch.cat(X_list)
    y = torch.cat(y_list)
    model.eval()
    with torch.no_grad():
        acc = (model(X).argmax(1) == y).float().mean().item()
    return acc


def train():
    torch.manual_seed(0)
    np.random.seed(0)

    global_model = ClientModel()
    server = FedAvgServer(global_model)

    # One noisy client with 10x more data (client 0)
    client_data = []
    n_samples_list = []
    for cid in range(8):
        is_noisy = (cid == 0)
        n = 117 * 10 if is_noisy else 117
        X, y = make_client_data(cid, n, is_noisy=is_noisy)
        client_data.append((X, y))
        n_samples_list.append(n)

    history = []
    for rnd in range(25):
        current_global = server.distribute()
        updates = []
        for cid in range(8):
            client = FedAvgClient(current_global, cid, lr=0.005)
            X, y = client_data[cid]
            update = client.local_train(X, y, n_epochs=3)
            updates.append(update)

        server.aggregate(updates, n_samples_list)
        acc = evaluate(server.global_model)

        if (rnd + 1) % 5 == 0:
            history.append({"round": rnd + 1, "acc": acc})
            print(f"Round {rnd+1}/{25} acc={acc:.4f}")

    final_acc = evaluate(server.global_model)
    results = {
        "final_acc": final_acc,
        "converged": final_acc > 0.5,
        "noisy_client_size": 117 * 10,
        "clean_client_size": 117,
        "history": history,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Final acc: {final_acc:.4f}")
    return results


if __name__ == "__main__":
    train()
