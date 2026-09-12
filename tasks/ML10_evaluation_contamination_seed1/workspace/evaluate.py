"""Evaluation with normalization/PCA contamination."""
import numpy as np
import json
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import accuracy_score


N_FEATURES = 24
N_CLASSES = 2
RANDOM_STATE = 1


def generate_data():
    X, y = make_classification(n_samples=668, n_features=N_FEATURES,
                                n_classes=N_CLASSES, n_informative=10, random_state=RANDOM_STATE)
    return X.astype(np.float32), y


def evaluate():
    X, y = generate_data()

    # BUG 1: Scaler fitted on full dataset before split
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)  # Uses test set statistics

    # BUG 2: PCA on full dataset
    pca = PCA(n_components=min(10, N_FEATURES), random_state=RANDOM_STATE)
    X_pca = pca.fit_transform(X_scaled)  # Leaks test variance

    # BUG 3: Outlier removal on full data
    iso = IsolationForest(contamination=0.05, random_state=RANDOM_STATE)
    mask = iso.fit_predict(X_pca) == 1  # Removes test outliers

    X_clean = X_pca[mask]
    y_clean = y[mask]

    # Split after all preprocessing (wrong)
    X_train, X_test, y_train, y_test = train_test_split(
        X_clean, y_clean, test_size=0.25, random_state=RANDOM_STATE
    )

    clf = RandomForestClassifier(n_estimators=50, random_state=RANDOM_STATE)
    clf.fit(X_train, y_train)
    acc = clf.score(X_test, y_test)

    results = {
        "test_accuracy": float(acc),
        "scaler_fitted_on_full_data": True,   # BUG
        "pca_fitted_on_full_data": True,      # BUG
        "outliers_removed_from_test": True,   # BUG
    }

    with open("eval_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Test accuracy: {acc:.3f} (WARNING: contaminated!)")
    return results


if __name__ == "__main__":
    evaluate()
