"""Hyperparameter search for SVM — contains invalid parameter combinations."""
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
import json
import itertools


def get_data(seed=2):
    X, y = make_classification(n_samples=546, n_features=10,
                                n_classes=2, n_informative=8, random_state=seed)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=seed)
    sc = StandardScaler()
    return sc.fit_transform(X_tr), sc.transform(X_te), y_tr, y_te


def search():
    X_tr, X_te, y_tr, y_te = get_data()

    # BUG 1: C <= 0 included
    C_values = [-1.0, 0.0, 0.1, 1.0, 10.0, 100.0]  # First two invalid

    # BUG 2: gamma=0 included
    gamma_values = [0, 0.001, 0.01, "scale"]  # gamma=0 is invalid

    # BUG 3: degree passed for non-poly kernels
    kernels_with_degree = [
        {"kernel": "rbf", "degree": 3},    # degree irrelevant for rbf
        {"kernel": "linear", "degree": 2}, # degree irrelevant for linear
        {"kernel": "poly", "degree": 3},   # Only this is valid
    ]

    tried = []
    best_acc = 0.0
    best_params = None
    invalid_count = 0

    for C, gamma, kd in itertools.product(C_values[:4], gamma_values[:3], kernels_with_degree[:2]):
        params = {"C": C, "gamma": gamma, **kd}
        try:
            clf = SVC(C=C, gamma=gamma, kernel=kd["kernel"], random_state=2)
            clf.fit(X_tr, y_tr)
            acc = clf.score(X_te, y_te)
        except (ValueError, Exception):
            acc = 0.0
            invalid_count += 1
        tried.append({"params": params, "accuracy": acc})
        if acc > best_acc:
            best_acc = acc
            best_params = params

    results = {
        "n_trials": len(tried),
        "best_accuracy": best_acc,
        "best_params": best_params,
        "invalid_combos_tried": invalid_count,
        "trials": tried[:5],
    }

    with open("search_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Best accuracy: {best_acc:.3f}")
    return results


if __name__ == "__main__":
    search()
