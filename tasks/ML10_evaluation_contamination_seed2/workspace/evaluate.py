"""Cross-validation evaluation with leakage bugs."""
import numpy as np
import json
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
import numpy as np


N_FEATURES = 16
N_CLASSES = 2
RANDOM_STATE = 2


def generate_data():
    X, y = make_classification(n_samples=628, n_features=N_FEATURES,
                                n_classes=N_CLASSES, n_informative=10, random_state=RANDOM_STATE)
    return X.astype(np.float32), y


def evaluate():
    X, y = generate_data()

    # BUG 2: Test set included in cross-validation
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=RANDOM_STATE)

    # BUG 1: Preprocessing OUTSIDE CV loop (leaks fold statistics)
    scaler = StandardScaler()
    X_all_scaled = scaler.fit_transform(X)  # Fits on all data including test folds
    X_train_scaled = X_all_scaled[:len(X_train)]
    X_test_scaled = X_all_scaled[len(X_train):]

    # BUG 3: Feature selection outside CV
    selector = SelectKBest(f_classif, k=10)
    X_train_sel = selector.fit_transform(X_train_scaled, y_train)  # Outside CV
    X_test_sel = selector.transform(X_test_scaled)

    clf = RandomForestClassifier(n_estimators=50, random_state=RANDOM_STATE)

    # BUG 2: passing X (all data including test) to cross_val_score
    X_scaled_all = scaler.transform(X)
    X_sel_all = selector.transform(X_scaled_all)
    cv_scores = cross_val_score(clf, X_sel_all, y, cv=5)  # Uses test set in CV!

    clf.fit(X_train_sel, y_train)
    test_acc = clf.score(X_test_sel, y_test)

    results = {
        "cv_mean_score": float(cv_scores.mean()),
        "test_accuracy": float(test_acc),
        "preprocessing_outside_cv": True,   # BUG
        "test_set_in_cv": True,             # BUG
        "feature_selection_outside_cv": True,  # BUG
    }

    with open("eval_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"CV score: {cv_scores.mean():.3f}, Test acc: {test_acc:.3f} (contaminated!)")
    return results


if __name__ == "__main__":
    evaluate()
