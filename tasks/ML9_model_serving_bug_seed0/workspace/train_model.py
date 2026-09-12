"""Training script — saves model and preprocessing artifacts."""
import numpy as np
import json
import pickle
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


N_FEATURES = 15
N_CLASSES = 3


def train(seed=0):
    np.random.seed(seed)
    X, y = make_classification(n_samples=932, n_features=N_FEATURES,
                                n_classes=N_CLASSES, n_informative=10, random_state=seed)
    X = X.astype(np.float32)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=seed)

    # Preprocessing: normalize using TRAINING set statistics
    train_mean = X_train.mean(axis=0)
    train_std = X_train.std(axis=0) + 1e-8

    X_train_norm = (X_train - train_mean) / train_std
    X_test_norm = (X_test - train_mean) / train_std

    # Clip to [-3, 3] sigma (applied during training)
    X_train_norm = np.clip(X_train_norm, -3, 3)
    X_test_norm = np.clip(X_test_norm, -3, 3)

    # Train on ALL 15 features (no column dropping)
    clf = RandomForestClassifier(n_estimators=50, random_state=seed)
    clf.fit(X_train_norm, y_train)

    acc = clf.score(X_test_norm, y_test)
    print(f"Training accuracy: {acc:.3f}")

    # Save artifacts
    artifacts = {
        "train_mean": train_mean.tolist(),
        "train_std": train_std.tolist(),
        "n_features": N_FEATURES,
        "clip_range": [-3, 3],
        "drop_feature_0": False,  # Do NOT drop any features
    }
    with open("preprocessing_artifacts.json", "w") as f:
        json.dump(artifacts, f, indent=2)

    with open("model.pkl", "wb") as f:
        pickle.dump(clf, f)

    # Save test set for verification
    np.save("test_inputs.npy", X_test)
    test_preds = clf.predict(X_test_norm)
    np.save("test_predictions_reference.npy", test_preds)

    print("Saved model.pkl and preprocessing_artifacts.json")
    return acc


if __name__ == "__main__":
    train()
