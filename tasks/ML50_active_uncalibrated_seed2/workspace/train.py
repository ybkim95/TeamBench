"""Active learning training loop."""
import json
import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from query_strategy import EntropyStrategy, MCDropoutStrategy
from model import ActiveModel


def make_dataset(n_pool: int = 1200, n_test: int = 314,
                 input_dim: int = 24, n_classes: int = 5):
    torch.manual_seed(42)
    centers = torch.randn(n_classes, input_dim) * 1.5
    total = n_pool + n_test
    X_list, y_list = [], []
    per_class = total // n_classes
    for c in range(n_classes):
        X_list.append(centers[c] + 0.8 * torch.randn(per_class, input_dim))
        y_list.append(torch.full((per_class,), c, dtype=torch.long))
    X = torch.cat(X_list)
    y = torch.cat(y_list)
    perm = torch.randperm(len(X))
    X, y = X[perm], y[perm]
    return X[:n_pool], y[:n_pool], X[n_pool:], y[n_pool:]


def train_model(model, X_labeled, y_labeled, n_epochs: int = 22, lr: float = 0.001):
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    model.train()
    for _ in range(n_epochs):
        perm = torch.randperm(len(X_labeled))
        for i in range(0, len(X_labeled), 32):
            idx = perm[i:i+32]
            optimizer.zero_grad()
            loss = criterion(model(X_labeled[idx]), y_labeled[idx])
            loss.backward()
            optimizer.step()


def evaluate(model, X_test, y_test):
    model.eval()
    with torch.no_grad():
        acc = (model(X_test).argmax(1) == y_test).float().mean().item()
    return acc


def run_active_learning(strategy, X_pool, y_pool, X_test, y_test,
                        initial: int = 25,
                        query_size: int = 25,
                        n_rounds: int = 10):
    torch.manual_seed(0)
    np.random.seed(0)

    pool_mask = torch.ones(len(X_pool), dtype=torch.bool)
    # Initial labeled set
    labeled_idx = list(range(initial))
    for i in labeled_idx:
        pool_mask[i] = False

    accs = []
    for rnd in range(n_rounds):
        X_labeled = X_pool[labeled_idx]
        y_labeled = y_pool[labeled_idx]

        model = ActiveModel()
        train_model(model, X_labeled, y_labeled)
        acc = evaluate(model, X_test, y_test)
        accs.append(acc)

        # Query new samples from pool
        pool_indices = pool_mask.nonzero().squeeze(1)
        if len(pool_indices) < query_size:
            break
        X_pool_remaining = X_pool[pool_indices]
        selected = strategy.select(model, X_pool_remaining, query_size)
        new_idx = pool_indices[selected].tolist()
        labeled_idx.extend(new_idx)
        for i in new_idx:
            pool_mask[i] = False

    return accs, len(labeled_idx)


def compute_auc(accs):
    """Area under the learning curve (normalized)."""
    if not accs:
        return 0.0
    return sum(accs) / len(accs)


def train():
    torch.manual_seed(0)
    X_pool, y_pool, X_test, y_test = make_dataset()

    # Compare entropy (buggy) vs MC Dropout (correct)
    entropy_strat = EntropyStrategy()
    mc_strat = MCDropoutStrategy()

    entropy_accs, _ = run_active_learning(entropy_strat, X_pool.clone(), y_pool.clone(),
                                           X_test, y_test)
    mc_accs, n_labeled = run_active_learning(mc_strat, X_pool.clone(), y_pool.clone(),
                                              X_test, y_test)

    entropy_auc = compute_auc(entropy_accs)
    mc_auc = compute_auc(mc_accs)

    results = {
        "entropy_accs": entropy_accs,
        "mc_accs": mc_accs,
        "entropy_auc": entropy_auc,
        "mc_auc": mc_auc,
        "converged": mc_auc > 0.65,
        "mc_better": mc_auc > entropy_auc,
        "n_labeled_final": n_labeled,
    }
    with open("training_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Entropy AUC: {entropy_auc:.4f}, MC Dropout AUC: {mc_auc:.4f}")
    print(f"MC better: {mc_auc > entropy_auc}")
    return results


if __name__ == "__main__":
    train()
