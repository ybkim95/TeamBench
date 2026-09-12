"""Inference/serving script — contains preprocessing inconsistencies."""
import numpy as np
import json
import pickle


def load_model():
    with open("model.pkl", "rb") as f:
        return pickle.load(f)


def preprocess_inference(X):
    """
    Inference preprocessing — BUGGY: inconsistent with training.
    """
    # BUG 1: Using per-batch stats instead of training set stats
    batch_mean = X.mean(axis=0)   # Should load from preprocessing_artifacts.json
    batch_std = X.std(axis=0) + 1e-8  # Should use train_std, not batch_std
    X_norm = (X - batch_mean) / batch_std

    # BUG 2: Missing feature clipping (training used clip(-3, 3))
    # X_norm = np.clip(X_norm, -3, 3)  # This line is missing

    # BUG 3: Incorrectly dropping first feature (thinking it's an ID)
    X_norm = X_norm[:, 1:]  # Wrong: training used ALL features

    return X_norm


def predict(X):
    """Run inference."""
    model = load_model()
    X_processed = preprocess_inference(X)
    return model.predict(X_processed)


def main():
    # Load test inputs saved by training
    X_test = np.load("test_inputs.npy")
    ref_preds = np.load("test_predictions_reference.npy")

    preds = predict(X_test)

    # Check agreement with reference
    try:
        agreement = (preds == ref_preds).mean()
    except ValueError:
        agreement = 0.0  # Shape mismatch

    results = {
        "n_samples": len(X_test),
        "agreement_with_training": float(agreement),
        "predictions_match": agreement > 0.95,
    }

    with open("serving_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Agreement with training predictions: {agreement:.3f}")
    return results


if __name__ == "__main__":
    main()
