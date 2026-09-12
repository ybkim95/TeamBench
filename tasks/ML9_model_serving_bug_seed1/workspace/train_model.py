"""Training script for NLP model — saves vectorizer and model."""
import numpy as np
import json
import pickle
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


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
LABELS = [1, 0, 1, 1, 0, 1, 0, 1]


def clean_text(text: str) -> str:
    """Training text cleaning pipeline."""
    text = text.lower()                          # Lowercase
    text = re.sub(r"[^\w\s]", "", text)         # Remove punctuation
    text = text.strip()
    return text


def train(seed=1):
    np.random.seed(seed)

    # Clean texts using training pipeline
    cleaned = [clean_text(t) for t in SAMPLE_TEXTS]

    # Fit TF-IDF on training data
    vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
    X = vectorizer.fit_transform(cleaned).toarray().astype(np.float32)
    y = np.array(LABELS)

    # Train model
    clf = LogisticRegression(random_state=seed, max_iter=200)
    clf.fit(X, y)
    acc = clf.score(X, y)
    print(f"Training accuracy: {acc:.3f}")

    # Save artifacts
    with open("vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)
    with open("model.pkl", "wb") as f:
        pickle.dump(clf, f)

    artifacts = {
        "do_lowercase": True,
        "remove_punctuation": True,
        "max_features": 10000,
        "ngram_range": [1, 2],
    }
    with open("preprocessing_artifacts.json", "w") as f:
        json.dump(artifacts, f, indent=2)

    # Save reference predictions
    np.save("test_predictions_reference.npy", clf.predict(X))
    print("Saved vectorizer.pkl, model.pkl, preprocessing_artifacts.json")
    return acc


if __name__ == "__main__":
    train()
