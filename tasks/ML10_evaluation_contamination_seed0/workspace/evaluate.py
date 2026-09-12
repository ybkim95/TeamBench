"""Evaluation script — contains 3 test set contamination bugs."""
import numpy as np
import json
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import mutual_info_classif
from sklearn.metrics import accuracy_score


N_FEATURES = 21
N_CLASSES = 2
RANDOM_STATE = 0


def generate_data():
    X, y = make_classification(n_samples=797, n_features=N_FEATURES,
                                n_classes=N_CLASSES, n_informative=10, random_state=RANDOM_STATE)
    return X.astype(np.float32), y


def target_encode(X, y, col_idx):
    """Target encode column col_idx using label means."""
    encoded = X.copy()
    classes = np.unique(y)
    for c in classes:
        mask = y == c
        # Map values near class c's mean
        encoded[mask, col_idx] = y[mask].mean()
    return encoded


def evaluate():
    X, y = generate_data()

    # BUG 1: Target encoding computed on FULL dataset before split
    X_encoded = target_encode(X, y, col_idx=0)  # Uses all labels including test

    # BUG 2: Feature selection on FULL dataset
    mi_scores = mutual_info_classif(X_encoded, y, random_state=RANDOM_STATE)  # Uses test labels
    top_features = np.argsort(mi_scores)[-10:]
    X_selected = X_encoded[:, top_features]

    # Split AFTER feature engineering (wrong order)
    X_train, X_test, y_train, y_test = train_test_split(
        X_selected, y, test_size=0.25, random_state=RANDOM_STATE, stratify=y
    )

    # Train model
    clf = RandomForestClassifier(n_estimators=50, random_state=RANDOM_STATE)
    clf.fit(X_train, y_train)

    # BUG 3: Threshold tuning on test set
    test_probs = clf.predict_proba(X_test)
    best_thresh = 0.5
    best_test_acc = 0
    thresholds = np.linspace(0.1, 0.9, 17)
    for thresh in thresholds:
        preds = (test_probs[:, 1] >= thresh).astype(int)
        acc = accuracy_score(y_test, preds)
        if acc > best_test_acc:
            best_test_acc = acc
            best_thresh = thresh  # Tuned on test set — CONTAMINATION!

    final_preds = (test_probs[:, 1] >= best_thresh).astype(int)
    final_acc = accuracy_score(y_test, final_preds)

    results = {
        "test_accuracy": float(final_acc),
        "threshold_used": float(best_thresh),
        "n_features_selected": int(len(top_features)),
        "target_encoding_applied_before_split": True,  # BUG flag
        "feature_selection_applied_before_split": True,  # BUG flag
        "threshold_tuned_on_test": True,  # BUG flag
    }

    with open("eval_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Test accuracy: {final_acc:.3f} (WARNING: contaminated!)")
    return results


if __name__ == "__main__":
    evaluate()
