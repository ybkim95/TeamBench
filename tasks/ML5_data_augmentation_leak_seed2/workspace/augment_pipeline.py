"""Data augmentation pipeline for ECG time series classification with signal augmentation."""
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import json


N_ORIGINAL    = 600
N_FEATURES    = 11
N_CLASSES     = 3
AUG_FACTOR    = 4
TEST_SIZE     = 0.2
RANDOM_STATE  = 2

AUGMENTATION_SEED = 42

AUGMENTATION_OPS = ["add_gaussian_noise", "time_warp", "amplitude_scale"]

LABEL_SMOOTHING = 0.1

TTA_COPIES = 4


def load_data():
    """Load synthetic ecg_classification dataset."""
    np.random.seed(2)
    X = np.random.randn(N_ORIGINAL, N_FEATURES).astype(np.float32)
    centers = np.random.randn(N_CLASSES, N_FEATURES)
    dists = np.linalg.norm(X[:, None] - centers[None], axis=2)
    y = dists.argmin(axis=1)
    return X, y


def augment_data(X, y):
    """Augment dataset by AUGMENTATION_SEED-seeded noise copies."""
    np.random.seed(AUGMENTATION_SEED)  # intentional fixed seed
    X_list, y_list = [X], [y]
    for _ in range(AUG_FACTOR - 1):
        X_list.append(X + np.random.randn(*X.shape) * 0.05)
        y_list.append(y)
    return np.vstack(X_list), np.concatenate(y_list)


def apply_label_smoothing(y, n_classes, epsilon):
    """Convert integer labels to smoothed soft targets."""
    n = len(y)
    y_smooth = np.full((n, n_classes), epsilon / n_classes, dtype=np.float32)
    y_smooth[np.arange(n), y] = 1.0 - epsilon + epsilon / n_classes
    return y_smooth


def tta_predict(model, X, scaler):
    """Test-time augmentation: average predictions over TTA_COPIES perturbed copies."""
    np.random.seed(AUGMENTATION_SEED)  # reproducible TTA
    all_proba = []
    for _ in range(TTA_COPIES):
        X_noisy = X + np.random.randn(*X.shape) * 0.05
        X_scaled = scaler.transform(X_noisy)
        all_proba.append(model.predict_proba(X_scaled))
    avg_proba = np.mean(all_proba, axis=0)
    return avg_proba.argmax(axis=1)


def train_pipeline():
    """Train with augmentation."""
    X, y = load_data()

    X_aug, y_aug = augment_data(X, y)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_aug)

    # Split AFTER augmentation and scaling — both bugs compound here
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_aug, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y_aug
    )

    y_train_smooth = apply_label_smoothing(y_train, N_CLASSES, LABEL_SMOOTHING)

    model = RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE)
    model.fit(X_train, y_train)

    y_pred_tta = tta_predict(model, X_test, scaler)
    test_acc_tta = accuracy_score(y_test, y_pred_tta)
    train_acc = accuracy_score(y_train, model.predict(X_train))

    results = {
        "n_original":                     N_ORIGINAL,
        "n_train":                        len(X_train),
        "n_test":                         len(X_test),
        "augmentation_applied_before_split": True,   # bug flag
        "normalization_applied_before_split": True,  # bug flag
        "label_smoothing_preserved":      True,      # intentional flag
        "augmentation_seed_preserved":    True,      # intentional flag
        "tta_preserved":                  True,      # intentional flag
        "train_accuracy":                 float(train_acc),
        "test_accuracy_tta":              float(test_acc_tta),
        "augmentation_ops":               AUGMENTATION_OPS,
        "tta_copies":                     TTA_COPIES,
        "label_smoothing":                LABEL_SMOOTHING,
        "augmentation_seed":              AUGMENTATION_SEED,
    }

    with open("pipeline_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Train size: {len(X_train)} | Test size: {len(X_test)}")
    print(f"Train acc : {train_acc:.3f} | Test acc (TTA): {test_acc_tta:.3f}")
    return results


if __name__ == "__main__":
    train_pipeline()
