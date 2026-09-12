"""Hyperparameter search for neural network — contains invalid search space."""
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import json
import itertools


def get_data(seed=0):
    X, y = make_classification(n_samples=888, n_features=16,
                                n_classes=3, n_informative=8, random_state=seed)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=seed)
    sc = StandardScaler()
    return (sc.fit_transform(X_tr).astype(np.float32), y_tr.astype(np.int64),
            sc.transform(X_te).astype(np.float32), y_te.astype(np.int64))


def build_model(n_features, n_classes, hidden=64, dropout=0.3):
    return nn.Sequential(
        nn.Linear(n_features, hidden), nn.ReLU(), nn.Dropout(dropout),
        nn.Linear(hidden, n_classes)
    )


def train_eval(params, X_tr, y_tr, X_te, y_te):
    """Train model with given params, return val accuracy."""
    try:
        model = build_model(16, 3,
                            hidden=params.get("hidden", 64),
                            dropout=params.get("dropout", 0.3))
        # BUG 1: momentum passed to Adam (only valid for SGD)
        optimizer_kwargs = {"lr": params["lr"], "momentum": params.get("momentum", 0.9)}
        opt = optim.Adam(model.parameters(), **optimizer_kwargs)  # Adam ignores momentum, but crashes
        crit = nn.CrossEntropyLoss()
        Xt = torch.tensor(X_tr); yt = torch.tensor(y_tr)
        for _ in range(20):
            opt.zero_grad()
            loss = crit(model(Xt), yt)
            loss.backward(); opt.step()
        with torch.no_grad():
            acc = (model(torch.tensor(X_te)).argmax(1) == torch.tensor(y_te)).float().mean().item()
        return acc
    except Exception as e:
        return 0.0  # Invalid combo silently returns 0


def search():
    X_tr, y_tr, X_te, y_te = get_data()

    # BUG 2: Learning rates include very large values (logspace with wrong sign)
    learning_rates = list(np.logspace(4, 1, 5))  # [10000, 3162, ...] — should be logspace(-4, -1, 5)

    # BUG 3: Dropout >0.9 in search space — kills gradient flow
    dropouts = [0.1, 0.3, 0.5, 0.92, 0.97]  # Last two are invalid

    # BUG 1: momentum in search space for Adam
    momentums = [0.85, 0.9, 0.95]

    hiddens = [32, 64, 128]

    tried = []
    best_acc = 0.0
    best_params = None

    for lr, dropout, momentum, hidden in itertools.product(learning_rates, dropouts, momentums, hiddens):
        params = {"lr": lr, "dropout": dropout, "momentum": momentum, "hidden": hidden}
        acc = train_eval(params, X_tr, y_tr, X_te, y_te)
        tried.append({"params": params, "accuracy": acc})
        if acc > best_acc:
            best_acc = acc
            best_params = params

    results = {
        "n_trials": len(tried),
        "best_accuracy": best_acc,
        "best_params": best_params,
        "invalid_combos_tried": sum(
            1 for t in tried
            if t["params"]["lr"] > 1.0 or t["params"]["dropout"] > 0.9
        ),
        "trials": tried[:5],  # sample
    }

    with open("search_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Best accuracy: {best_acc:.3f} with params: {best_params}")
    return results


if __name__ == "__main__":
    search()
