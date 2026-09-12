"""Inference/serving script for NLP model — contains preprocessing bugs."""
import numpy as np
import json
import pickle
import re
from sklearn.feature_extraction.text import TfidfVectorizer


SAMPLE_TEXTS = [
    "This product is absolutely amazing and works perfectly.",
    "Terrible quality, completely disappointed with this purchase.",
    "Average experience, nothing special about it at all.",
    "Great value for money, highly recommend to everyone!",
    "Broken on arrival, waste of money and time.",
    "Exceeded my expectations in every possible way.",
    "Would not buy again, poor customer service too.",
    "Decent product for the price, does what it says.",
]


def preprocess_inference(texts):
    """
    Inference preprocessing — BUGGY: inconsistent with training.
    """
    # BUG 1: Not lowercasing (training did lowercase)
    # texts = [t.lower() for t in texts]  # Missing!
    cleaned = [re.sub(r"[^\w\s]", "", t).strip() for t in texts]  # No lowercase

    # BUG 2: Re-fitting vectorizer on inference batch
    # Should load the saved vectorizer and call .transform(), not .fit_transform()
    new_vectorizer = TfidfVectorizer(max_features=5000)  # BUG 3: wrong max_features (5000 vs 10000)
    X = new_vectorizer.fit_transform(cleaned).toarray().astype(np.float32)  # fit_transform is wrong

    return X


def predict(texts):
    with open("model.pkl", "rb") as f:
        model = pickle.load(f)
    X = preprocess_inference(texts)
    try:
        return model.predict(X)
    except Exception:
        return np.zeros(len(texts), dtype=int)


def main():
    ref_preds = np.load("test_predictions_reference.npy")
    preds = predict(SAMPLE_TEXTS)

    try:
        agreement = (preds == ref_preds).mean()
    except Exception:
        agreement = 0.0

    results = {
        "n_samples": len(SAMPLE_TEXTS),
        "agreement_with_training": float(agreement),
        "predictions_match": agreement > 0.95,
    }

    with open("serving_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Agreement with training predictions: {agreement:.3f}")
    return results


if __name__ == "__main__":
    main()
