"""Hyperparameter search for gradient boosting — contains invalid search space."""
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import GradientBoostingClassifier
import json
import itertools


def get_data(seed=1):
    X, y = make_classification(n_samples=791, n_features=12,
                                n_classes=2, n_informative=8, random_state=seed)
    return train_test_split(X, y, test_size=0.2, random_state=seed)


def search():
    X_tr, X_te, y_tr, y_te = get_data()

    # BUG 1: n_estimators=0 is invalid
    n_estimators_list = [0, 10, 50, 100, 200]  # 0 is invalid

    # BUG 2: negative/zero learning rates
    learning_rates = list(np.logspace(3, -3, 5))  # Wrong: should be logspace(-3, 0, 5)
    # logspace(3, -3) = [1000, ..., 0.001] — includes values >1 which are technically
    # valid but suboptimal; includes negatives via wrong linspace elsewhere

    # BUG 3: subsample >1.0
    subsamples = [0.6, 0.8, 1.0, 1.2, 1.5]  # Last two are invalid (>1.0)

    tried = []
    best_acc = 0.0
    best_params = None
    invalid_count = 0

    for n_est, lr, sub in itertools.product(n_estimators_list[:3], learning_rates[:3], subsamples[:4]):
        params = {"n_estimators": n_est, "learning_rate": lr, "subsample": sub}
        try:
            clf = GradientBoostingClassifier(
                n_estimators=n_est, learning_rate=lr, subsample=sub, random_state=1
            )
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
